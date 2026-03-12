"""
Partition Flasher Module
Flashes firmware partitions to MTK device
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, Optional, Callable
import time


class PartitionFlasher:
    """Flash partitions to MTK device"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.adb_path = Path(self.config.get("tools_dir", "./tools")) / "platform-tools" / "adb.exe"
        self.fastboot_path = Path(self.config.get("tools_dir", "./tools")) / "platform-tools" / "fastboot.exe"
    
    def flash_partitions(
        self, 
        partitions: Dict[str, str],
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        status_callback: Optional[Callable[[str, int], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None
    ) -> bool:
        """Flash partitions to device
        
        Args:
            partitions: Dict of partition_name -> file_path
            progress_callback: Called with (partition_name, current, total)
            status_callback: Called with (partition_name, percentage)
            cancel_check: Called to check if cancellation requested
        
        Returns:
            True if successful, False otherwise
        """
        
        if not self._is_device_connected():
            self.logger.error("Device not connected")
            return False
        
        try:
            # Reboot to bootloader
            self.logger.info("Rebooting device to bootloader...")
            self._run_adb(["reboot", "bootloader"])
            time.sleep(3)
            
            # Check for cancellation
            if cancel_check and cancel_check():
                self.logger.info("Flashing cancelled by user")
                return False
            
            # Verify fastboot connection
            if not self._is_fastboot_connected():
                self.logger.error("Device not found in fastboot mode")
                return False
            
            # Calculate total partitions
            total_partitions = len(partitions)
            current = 0
            
            # Flash each partition
            for partition_name, partition_file in partitions.items():
                # Check for cancellation
                if cancel_check and cancel_check():
                    self.logger.info("Flashing cancelled by user")
                    return False
                
                current += 1
                
                if progress_callback:
                    progress_callback(partition_name, current, total_partitions)
                
                file_path = Path(partition_file)
                if not file_path.exists():
                    self.logger.warning(f"Partition file not found: {partition_file}")
                    continue
                
                self.logger.info(f"Flashing {partition_name}...")
                
                # Create a progress callback for this partition
                def make_partition_progress(name, callback):
                    def partition_progress(percent):
                        if callback:
                            callback(name, percent)
                    return partition_progress
                
                partition_progress = make_partition_progress(partition_name, status_callback)
                
                # Determine flash command based on partition name
                if partition_name.lower() == 'super':
                    # Super partition requires special handling
                    success = self._flash_super_with_progress(file_path, partition_progress)
                elif partition_name.lower() == 'boot':
                    success = self._flash_boot_with_progress(file_path, partition_progress)
                elif partition_name.lower() == 'system':
                    success = self._flash_system_with_progress(file_path, partition_progress)
                elif partition_name.lower() == 'vendor':
                    success = self._flash_vendor_with_progress(file_path, partition_progress)
                else:
                    # Generic flash
                    success = self._run_fastboot(["flash", partition_name, str(file_path)], partition_progress)
                
                if success:
                    self.logger.info(f"Successfully flashed {partition_name}")
                    if status_callback:
                        status_callback(partition_name, 100)
                else:
                    self.logger.error(f"Failed to flash {partition_name}")
                    if status_callback:
                        status_callback(partition_name, -1)
            
            # Check for cancellation before reboot
            if cancel_check and cancel_check():
                self.logger.info("Flashing cancelled by user before reboot")
                return False
            
            # Reboot device
            self.logger.info("Rebooting device...")
            self._run_fastboot(["reboot"], None)
            
            self.logger.info("Flashing completed successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Flashing failed: {e}")
            return False
    
    def _flash_super(self, file_path: Path) -> bool:
        """Flash super partition"""
        return self._run_fastboot(["flash", "super", str(file_path)])
    
    def _flash_super_with_progress(self, file_path: Path, progress_callback: Optional[Callable[[int], None]] = None) -> bool:
        """Flash super partition with progress"""
        return self._run_fastboot(["flash", "super", str(file_path)], progress_callback)
    
    def _flash_boot(self, file_path: Path) -> bool:
        """Flash boot partition"""
        return self._run_fastboot(["flash", "boot", str(file_path)])
    
    def _flash_boot_with_progress(self, file_path: Path, progress_callback: Optional[Callable[[int], None]] = None) -> bool:
        """Flash boot partition with progress"""
        return self._run_fastboot(["flash", "boot", str(file_path)], progress_callback)
    
    def _flash_system(self, file_path: Path) -> bool:
        """Flash system partition"""
        # Try different methods
        methods = [
            ["flash", "system", str(file_path)],
            ["flash", "system_a", str(file_path)],
            ["flash", "system_b", str(file_path)],
        ]
        
        for method in methods:
            if self._run_fastboot(method):
                return True
        return False
    
    def _flash_system_with_progress(self, file_path: Path, progress_callback: Optional[Callable[[int], None]] = None) -> bool:
        """Flash system partition with progress"""
        methods = [
            ["flash", "system", str(file_path)],
            ["flash", "system_a", str(file_path)],
            ["flash", "system_b", str(file_path)],
        ]
        
        for method in methods:
            if self._run_fastboot(method, progress_callback):
                return True
        return False
    
    def _flash_vendor(self, file_path: Path) -> bool:
        """Flash vendor partition"""
        methods = [
            ["flash", "vendor", str(file_path)],
            ["flash", "vendor_a", str(file_path)],
            ["flash", "vendor_b", str(file_path)],
        ]
        
        for method in methods:
            if self._run_fastboot(method):
                return True
        return False
    
    def _flash_vendor_with_progress(self, file_path: Path, progress_callback: Optional[Callable[[int], None]] = None) -> bool:
        """Flash vendor partition with progress"""
        methods = [
            ["flash", "vendor", str(file_path)],
            ["flash", "vendor_a", str(file_path)],
            ["flash", "vendor_b", str(file_path)],
        ]
        
        for method in methods:
            if self._run_fastboot(method, progress_callback):
                return True
        return False
    
    def _is_device_connected(self) -> bool:
        """Check if device is connected via ADB"""
        try:
            result = self._run_adb(["devices", "-l"], check=False)
            return result and result.returncode == 0
        except Exception as e:
            self.logger.error(f"Failed to check device: {e}")
            return False
    
    def _is_fastboot_connected(self) -> bool:
        """Check if device is in fastboot mode"""
        try:
            result = subprocess.run(
                [str(self.fastboot_path), "devices"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return "fastboot" in result.stdout or result.returncode == 0
        except Exception as e:
            self.logger.error(f"Failed to check fastboot: {e}")
            return False
    
    def _run_adb(self, args: list, check: bool = True) -> Optional[subprocess.CompletedProcess]:
        """Run ADB command"""
        try:
            cmd = [str(self.adb_path)] + args
            self.logger.debug(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if check and result.returncode != 0:
                self.logger.error(f"ADB command failed: {result.stderr}")
                return None
            
            return result
        except Exception as e:
            self.logger.error(f"ADB execution failed: {e}")
            return None
    
    def _run_fastboot(self, args: list, progress_callback: Optional[Callable[[int], None]] = None) -> bool:
        """Run Fastboot command with progress updates"""
        try:
            cmd = [str(self.fastboot_path)] + args
            self.logger.info(f"Running: {' '.join(cmd)}")
            
            # Report start
            if progress_callback:
                progress_callback(1)
            
            # Run fastboot command (it handles progress internally)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for large partitions
            )
            
            # Log output
            if result.stdout:
                self.logger.debug(f"fastboot output: {result.stdout}")
            if result.stderr:
                self.logger.debug(f"fastboot stderr: {result.stderr}")
            
            # Report progress based on completion
            if progress_callback:
                if result.returncode == 0:
                    progress_callback(100)
                else:
                    progress_callback(50)  # Partial progress on failure
            
            if result.returncode != 0:
                self.logger.error(f"Fastboot command failed: {result.stderr or result.stdout}")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            self.logger.error("Fastboot command timed out")
            if progress_callback:
                progress_callback(0)  # Timeout = fail
            return False
        except Exception as e:
            self.logger.error(f"Fastboot execution failed: {e}")
            if progress_callback:
                progress_callback(0)
            return False
