"""
Android Emulator Integration
Launch Android emulator with extracted MTK partitions
"""

import os
import logging
import subprocess
import shutil
import ctypes
from pathlib import Path
from typing import Optional, Dict, Callable
import time


class AndroidEmulator:
    """Manage Android emulator for previewing firmware"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.emulator_process = None
        self.avd_name = "MTK_Preview_AVD"
        self.last_error = ""
        self.avd_home: Optional[Path] = None
        
        # Paths
        self.android_sdk = self._find_android_sdk()
        self.emulator_path = None
        self.avdmanager_path = None
        
        if self.android_sdk:
            self.emulator_path = self.android_sdk / "emulator" / "emulator.exe"
            self.avdmanager_path = self.android_sdk / "cmdline-tools" / "latest" / "bin" / "avdmanager.bat"

        # Use SDK's ADB if available, fallback to tools folder
        tools_dir = Path(self.config.get("tools_dir", "./tools"))
        sdk_adb = self.android_sdk / "platform-tools" / "adb.exe" if self.android_sdk else None
        
        if sdk_adb and sdk_adb.exists():
            self.adb_path = sdk_adb
            self.logger.info(f"Using SDK ADB: {sdk_adb}")
        else:
            self.adb_path = tools_dir / "platform-tools" / "adb.exe"
            self.logger.info(f"Using local ADB: {self.adb_path}")
    
    def _find_android_sdk(self) -> Optional[Path]:
        """Find Android SDK installation"""
        # Common Android SDK locations
        possible_paths = [
            Path(os.environ.get("ANDROID_HOME", "")),
            Path(os.environ.get("ANDROID_SDK_ROOT", "")),
            Path.home() / "AppData" / "Local" / "Android" / "Sdk",
            Path("C:/Android/Sdk"),
            Path("C:/Program Files/Android/Sdk"),
        ]
        
        for path in possible_paths:
            if path.exists() and (path / "emulator").exists():
                self.logger.info(f"Found Android SDK at: {path}")
                return path
        
        self.logger.warning("Android SDK not found")
        return None
    
    def is_available(self) -> bool:
        """Check if emulator is available"""
        return self.android_sdk is not None and self.emulator_path and self.emulator_path.exists()

    def _bring_emulator_window_to_front(self, retries: int = 20, delay_s: float = 0.5) -> bool:
        """Try to restore and focus Android Emulator window on Windows."""
        if os.name != "nt":
            return False

        user32 = ctypes.windll.user32
        found_hwnd = None

        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        def _callback(hwnd, _lparam):
            nonlocal found_hwnd
            if not user32.IsWindowVisible(hwnd):
                return True

            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True

            title_buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title_buf, length + 1)
            title = title_buf.value.lower()

            # Emulator titles are typically like: "Android Emulator - <AVD_NAME>"
            if "android emulator" in title or self.avd_name.lower() in title:
                found_hwnd = hwnd
                return False

            return True

        for _ in range(retries):
            found_hwnd = None
            user32.EnumWindows(EnumWindowsProc(_callback), 0)

            if found_hwnd:
                SW_RESTORE = 9
                SW_SHOW = 5
                user32.ShowWindow(found_hwnd, SW_RESTORE)
                user32.ShowWindow(found_hwnd, SW_SHOW)
                user32.SetForegroundWindow(found_hwnd)
                return True

            time.sleep(delay_s)

        return False

    def _list_adb_emulators(self) -> list[str]:
        """Return running emulator serials from `adb devices` (e.g. emulator-5554)."""
        if not self.adb_path.exists():
            return []

        try:
            proc = subprocess.run(
                [str(self.adb_path), "devices"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            serials: list[str] = []
            for line in proc.stdout.splitlines():
                line = line.strip()
                if line.startswith("emulator-") and "\tdevice" in line:
                    serials.append(line.split("\t", 1)[0])
            return serials
        except Exception as e:
            self.logger.warning(f"Failed listing ADB emulators: {e}")
            return []

    def _shutdown_stale_emulators(self):
        """Terminate old emulator instances so success is tied to the new launch."""
        serials = self._list_adb_emulators()
        for serial in serials:
            try:
                self.logger.info(f"Shutting down stale emulator target: {serial}")
                subprocess.run(
                    [str(self.adb_path), "-s", serial, "emu", "kill"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            except Exception as e:
                self.logger.warning(f"Failed to close stale emulator {serial}: {e}")

        # Windows fallback: ensure ghost emulator.exe processes are cleared.
        if os.name == "nt":
            try:
                subprocess.run(
                    ["taskkill", "/IM", "emulator.exe", "/F"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            except Exception:
                pass

        time.sleep(2)

    def _get_partition_mapping(self, partitions: Dict[str, str]) -> Dict[str, str]:
        """Build AVD image copy plan from available partitions."""
        mapping = {
            'system': 'system.img',
            'vendor': 'vendor.img',
            'boot': 'boot.img',
            'userdata': 'userdata.img',
        }

        has_system_vendor = ('system' in partitions and 'vendor' in partitions)
        if not has_system_vendor and 'super' in partitions:
            mapping['super'] = 'super.img'

        return mapping

    def _estimate_required_bytes(self, partitions: Dict[str, str]) -> int:
        """Estimate disk space required for AVD creation on target disk."""
        mapping = self._get_partition_mapping(partitions)
        copy_bytes = 0

        for part_name in mapping.keys():
            if part_name in partitions:
                src = Path(partitions[part_name])
                if src.exists():
                    copy_bytes += src.stat().st_size

        userdata_mb = int(self.config.get("preview.emulator_userdata_mb", 4096) or 4096)
        userdata_bytes = userdata_mb * 1024 * 1024

        # Safety overhead for temp/snapshots/metadata.
        overhead_bytes = 2 * 1024 * 1024 * 1024

        return copy_bytes + userdata_bytes + overhead_bytes

    def _has_enough_space(self, target_dir: Path, required_bytes: int) -> tuple[bool, int]:
        """Return (ok, free_bytes) for the target filesystem."""
        usage = shutil.disk_usage(target_dir)
        return usage.free >= required_bytes, usage.free

    def _resolve_avd_home(self, workspace_dir: Optional[Path]) -> Path:
        """Resolve where AVD files are stored (prefer external/workspace disk)."""
        configured = self.config.get("preview.avd_base_dir")
        if configured:
            return Path(configured)
        if workspace_dir:
            return workspace_dir / ".mtk_avd"
        return Path.home() / ".android" / "avd"
    
    def create_avd_from_partitions(self, partitions: Dict[str, str], workspace_dir: Path) -> bool:
        """Create AVD configuration using extracted partitions"""
        if not self.is_available():
            self.logger.error("Android SDK/Emulator not available")
            self.last_error = "Android SDK/Emulator not available"
            return False
        
        try:
            self.avd_home = self._resolve_avd_home(workspace_dir)
            self.avd_home.mkdir(parents=True, exist_ok=True)

            required_bytes = self._estimate_required_bytes(partitions)
            min_free_gb = float(self.config.get("preview.min_free_space_gb", 20) or 20)
            min_free_bytes = int(min_free_gb * 1024 * 1024 * 1024)
            required_with_floor = max(required_bytes, min_free_bytes)
            ok_space, free_bytes = self._has_enough_space(self.avd_home, required_with_floor)
            if not ok_space:
                req_gb = required_with_floor / (1024 ** 3)
                free_gb = free_bytes / (1024 ** 3)
                self.last_error = (
                    f"Insufficient disk space at {self.avd_home} "
                    f"(required ~{req_gb:.1f} GB, free ~{free_gb:.1f} GB)"
                )
                self.logger.error(self.last_error)
                return False

            # Create AVD directory
            avd_dir = self.avd_home / f"{self.avd_name}.avd"
            avd_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy partition images to AVD directory
            self._copy_partitions_to_avd(partitions, avd_dir)
            
            # Create AVD config
            self._create_avd_config(avd_dir, partitions)

            # Remove stale cache artifact that can crash qemu with format mismatch.
            stale_cache_qcow = avd_dir / "cache.img.qcow2"
            if stale_cache_qcow.exists():
                stale_cache_qcow.unlink(missing_ok=True)
            stale_cache_raw = avd_dir / "cache.img"
            if stale_cache_raw.exists():
                stale_cache_raw.unlink(missing_ok=True)
            
            # Create empty encryption key file to prevent encryption errors
            encryptionkey = avd_dir / "encryptionkey.img"
            if not encryptionkey.exists():
                encryptionkey.write_bytes(b'')
            
            self.logger.info(f"Created AVD: {self.avd_name}")
            self.last_error = ""
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create AVD: {e}")
            self.last_error = str(e)
            return False
    
    def _copy_partitions_to_avd(self, partitions: Dict[str, str], avd_dir: Path):
        """Copy partition images to AVD directory"""
        partition_mapping = self._get_partition_mapping(partitions)
        
        for part_name, img_name in partition_mapping.items():
            if part_name in partitions:
                src = Path(partitions[part_name])
                dst = avd_dir / img_name
                if src.exists():
                    self.logger.info(f"Copying {part_name} -> {img_name}")
                    shutil.copy2(src, dst)
    
    def _create_avd_config(self, avd_dir: Path, partitions: Dict[str, str]):
        """Create AVD configuration file"""
        api_level = "android-30"
        tag_id = "google_apis"
        abi_type = "x86_64"
        image_sysdir = None

        # Emulator requires a valid base system image path even if we override disk images.
        if self.android_sdk:
            system_images_root = self.android_sdk / "system-images"
            if system_images_root.exists():
                candidates = sorted(
                    [
                        p for p in system_images_root.rglob("*")
                        if p.is_dir() and (p / "system.img").exists()
                    ],
                    key=lambda p: str(p),
                    reverse=True,
                )
                if candidates:
                    chosen = candidates[0]
                    try:
                        rel = chosen.relative_to(self.android_sdk)
                        image_sysdir = str(rel).replace("\\", "/") + "/"

                        parts = rel.parts
                        # Expected: system-images/<api>/<tag>/<abi>
                        if len(parts) >= 4:
                            api_level = parts[1]
                            tag_id = parts[2]
                            abi_type = parts[3]
                    except Exception:
                        image_sysdir = None

        userdata_mb = int(self.config.get("preview.emulator_userdata_mb", 4096) or 4096)
        config_content = f"""
avd.ini.encoding=UTF-8
path={avd_dir}
path.rel=avd/{self.avd_name}.avd
target={api_level}

abi.type={abi_type}
tag.id={tag_id}
tag.display=Google APIs
image.sysdir.1={image_sysdir or 'system-images/android-36/google_apis/x86_64/'}

hw.cpu.arch={abi_type}
hw.cpu.ncore=4
hw.ramSize=2048
hw.lcd.density=480
hw.lcd.width=1080
hw.lcd.height=2340

disk.dataPartition.size={userdata_mb}M
disk.cachePartition=no
hw.sdCard=yes
hw.gpu.enabled=yes
hw.gpu.mode=auto

disk.encryption=no
hw.keyboard=yes
fastboot.forceFastBoot=no
"""
        
        # Write config.ini
        config_file = avd_dir / "config.ini"
        config_file.write_text(config_content)
        
        # Write AVD .ini file next to AVD home location
        avd_home = self.avd_home or (Path.home() / ".android" / "avd")
        avd_ini = avd_home / f"{self.avd_name}.ini"
        avd_ini.write_text(f"path={avd_dir}\n")
    
    def launch_emulator(self, partitions: Optional[Dict[str, str]] = None, workspace_dir: Optional[Path] = None) -> bool:
        """Launch Android emulator with partitions"""
        if not self.is_available():
            self.logger.error("Android Emulator not available")
            self.last_error = "Android Emulator not available"
            return False
        
        # Create/Update AVD if partitions provided
        if partitions and workspace_dir:
            if not self.create_avd_from_partitions(partitions, workspace_dir):
                return False

        # Ensure avd_home is resolved even when AVD was prepared earlier.
        if self.avd_home is None:
            self.avd_home = self._resolve_avd_home(workspace_dir)
        
        try:
            # Launch emulator as background process
            env = os.environ.copy()
            env["ANDROID_AVD_HOME"] = str(self.avd_home)
            env["ANDROID_EMULATOR_HOME"] = str(self.avd_home.parent)
            if self.android_sdk:
                env["ANDROID_SDK_ROOT"] = str(self.android_sdk)
                env["ANDROID_HOME"] = str(self.android_sdk)

            # Avoid inheriting Qt/runtime flags from the host app that can hide emulator UI.
            for key in (
                "QT_QPA_PLATFORM",
                "QT_PLUGIN_PATH",
                "QT_QPA_FONTDIR",
                "SDL_VIDEODRIVER",
                "ANDROID_EMULATOR_HEADLESS",
            ):
                env.pop(key, None)

            startupinfo = None
            creationflags = 0
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 1  # SW_SHOWNORMAL
                creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

            logs_dir = Path("logs")
            logs_dir.mkdir(parents=True, exist_ok=True)
            launch_log = logs_dir / f"emulator_launch_{int(time.time())}.log"

            base_cmd = [
                str(self.emulator_path),
                "-avd", self.avd_name,
                "-no-snapshot-load",
            ]
            profiles = [
                ["-gpu", "auto"],
                ["-gpu", "swiftshader_indirect", "-accel", "off"],
                ["-gpu", "angle_indirect", "-accel", "off"],
            ]

            for profile in profiles:
                cmd = base_cmd + profile
                self.logger.info(f"Launching emulator: {' '.join(cmd)}")

                with launch_log.open("a", encoding="utf-8", errors="ignore") as lf:
                    lf.write(f"\n=== Launch profile: {' '.join(profile)} ===\n")
                    self.emulator_process = subprocess.Popen(
                        cmd,
                        cwd=str(self.emulator_path.parent),
                        env=env,
                        startupinfo=startupinfo,
                        creationflags=creationflags,
                        stdout=lf,
                        stderr=lf,
                    )

                # Give emulator a few seconds to fail fast (common with invalid GPU/accel settings).
                time.sleep(6)
                if self.emulator_process.poll() is None:
                    if os.name == "nt":
                        # Best-effort: ensure emulator GUI is visible to the user.
                        self._bring_emulator_window_to_front(retries=8, delay_s=0.5)

                    self.logger.info(f"Emulator launched with PID: {self.emulator_process.pid}")
                    self.last_error = ""
                    return True

                code = self.emulator_process.returncode
                self.logger.warning(
                    f"Emulator exited quickly with code {code} using profile: {' '.join(profile)}"
                )

            # All profiles failed.
            launch_tail = ""
            try:
                lines = launch_log.read_text(encoding="utf-8", errors="ignore").splitlines()
                launch_tail = " | ".join(lines[-6:])
            except Exception:
                launch_tail = ""

            self.last_error = "Emulator failed to start (code 1). See emulator_launch log in logs/."
            if launch_tail:
                self.logger.error(f"Emulator launch tail: {launch_tail}")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to launch emulator: {e}")
            self.last_error = str(e)
            return False
    
    def launch_with_qemu(self, partitions: Dict[str, str], workspace_dir: Path) -> bool:
        """Launch QEMU directly with MTK partitions (alternative to Android Emulator)"""
        qemu_path = shutil.which("qemu-system-aarch64")
        
        if not qemu_path:
            self.logger.error("QEMU not found. Install QEMU for direct emulation.")
            self.last_error = "QEMU not found"
            return False
        
        try:
            # Build QEMU command for ARM64 Android
            kernel = partitions.get('boot')
            system = partitions.get('system') or partitions.get('super')
            
            if not kernel or not system:
                self.logger.error("Missing required partitions (boot/system)")
                self.last_error = "Missing required partitions (boot/system)"
                return False
            
            cmd = [
                qemu_path,
                "-M", "virt",
                "-cpu", "cortex-a57",
                "-m", "2048",
                "-kernel", kernel,
                "-drive", f"file={system},format=raw,if=virtio",
                "-append", "console=ttyAMA0 root=/dev/vda rw",
                "-nographic",
                "-serial", "mon:stdio"
            ]
            
            self.logger.info(f"Launching QEMU: {' '.join(cmd)}")
            
            self.emulator_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to launch QEMU: {e}")
            self.last_error = str(e)
            return False
    
    def stop_emulator(self):
        """Stop running emulator"""
        if self.emulator_process:
            try:
                self.emulator_process.terminate()
                self.emulator_process.wait(timeout=10)
                self.logger.info("Emulator stopped")
            except Exception as e:
                self.logger.error(f"Failed to stop emulator: {e}")
                self.emulator_process.kill()
            finally:
                self.emulator_process = None
    
    def is_running(self) -> bool:
        """Check if emulator is running"""
        return self.emulator_process is not None and self.emulator_process.poll() is None
    
    def get_status(self) -> str:
        """Get emulator status"""
        if not self.is_available():
            return "Emulator not configured"
        elif self.is_running():
            return f"Running (PID: {self.emulator_process.pid})"
        else:
            return "Stopped"

    def flash_partitions_to_emulator(
        self,
        partitions: Dict[str, str],
        workspace_dir: Path,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        status_callback: Optional[Callable[[str, int], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> bool:
        """Create/update AVD from partition images and boot it as a real emulator target."""
        try:
            if not self.is_available():
                self.logger.error("Android Emulator not available")
                self.last_error = "Android Emulator not available"
                return False

            if cancel_check and cancel_check():
                return False

            if progress_callback:
                progress_callback("Prepare AVD", 1, 4)

            if self.is_running():
                self.stop_emulator()

            ok = self.create_avd_from_partitions(partitions, workspace_dir)
            if not ok:
                return False

            if cancel_check and cancel_check():
                return False

            if progress_callback:
                progress_callback("Launch Emulator", 2, 4)

            # Prevent stale/background emulator instances from faking a successful boot.
            self._shutdown_stale_emulators()

            # AVD is already created; avoid creating it twice.
            if not self.launch_emulator(None, workspace_dir):
                return False

            if cancel_check and cancel_check():
                self.stop_emulator()
                return False

            if progress_callback:
                progress_callback("Wait for ADB", 3, 4)

            # Restart ADB server to ensure it detects the emulator
            self.logger.info("Restarting ADB server to sync with emulator...")
            try:
                subprocess.run([str(self.adb_path), "kill-server"], capture_output=True, timeout=5)
                time.sleep(1)
                subprocess.run([str(self.adb_path), "start-server"], capture_output=True, timeout=5)
                time.sleep(2)
            except Exception as e:
                self.logger.warning(f"Failed to restart ADB server: {e}")

            # Wait for emulator to appear in ADB and complete boot.
            ready = False
            for attempt in range(180):  # up to ~360s (6 minutes)
                if cancel_check and cancel_check():
                    self.stop_emulator()
                    return False

                if self.emulator_process and self.emulator_process.poll() is not None:
                    code = self.emulator_process.returncode
                    self.logger.error(f"Emulator process exited early with code {code}")
                    self.last_error = f"Emulator process exited early (code {code})"
                    return False

                try:
                    devices = subprocess.run(
                        [str(self.adb_path), "devices"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    # Log ADB output every 15 attempts (30 seconds)
                    if attempt % 15 == 0:
                        self.logger.info(f"ADB devices check (attempt {attempt}): {devices.stdout.strip()}")
                    
                    if "emulator-" in devices.stdout and "device" in devices.stdout:
                        ready = True
                        self.logger.info(f"Emulator appeared in ADB after {attempt*2}s")
                        break
                except Exception as e:
                    self.logger.debug(f"ADB check attempt {attempt}: {e}")
                time.sleep(2)

            if not ready:
                self.logger.error("Emulator did not appear in ADB after 360s")
                self.last_error = "Emulator did not appear in ADB. Check if Android Emulator is properly installed."
                return False

            # First boot with custom partitions can take 20+ minutes
            booted = False
            for attempt in range(600):  # up to ~1200s (20 minutes)
                if cancel_check and cancel_check():
                    self.stop_emulator()
                    return False

                if self.emulator_process and self.emulator_process.poll() is not None:
                    code = self.emulator_process.returncode
                    self.logger.error(f"Emulator process exited during boot with code {code}")
                    self.last_error = f"Emulator process exited during boot (code {code})"
                    return False

                try:
                    prop = subprocess.run(
                        [str(self.adb_path), "shell", "getprop", "sys.boot_completed"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    # Log progress every minute
                    if attempt % 30 == 0:
                        minutes = attempt * 2 / 60
                        self.logger.info(f"Boot check: {minutes:.1f} minutes elapsed, waiting for sys.boot_completed=1...")
                    
                    if prop.stdout.strip() == "1":
                        booted = True
                        self.logger.info(f"Emulator boot completed after {attempt*2}s")
                        break
                except Exception as e:
                    if attempt % 30 == 0:
                        self.logger.debug(f"Boot check attempt {attempt}: {e}")
                time.sleep(2)

            if not booted:
                self.logger.error("Emulator boot timeout after 1200s (20 minutes)")
                self.last_error = "Emulator took too long to boot. Check emulator window - it may still be booting."
                return False

            if os.name == "nt":
                if self._bring_emulator_window_to_front(retries=20, delay_s=0.5):
                    self.logger.info("Emulator window restored to foreground")
                else:
                    self.logger.warning("Emulator is running, but no emulator window was detected")

            if status_callback:
                for name in partitions.keys():
                    status_callback(name, 100)

            if progress_callback:
                progress_callback("Boot Completed", 4, 4)

            self.logger.info("Emulator launched successfully with firmware images")
            self.last_error = ""
            return True

        except Exception as e:
            self.logger.error(f"Failed to flash partitions to emulator: {e}")
            self.last_error = str(e)
            return False
