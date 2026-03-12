"""
Device Communication Module
Handles all device connections: ADB, Fastboot, MTK Preloader, MTK Download Mode
"""

import usb.core
import usb.util
import serial
import time
import logging
from typing import Optional, List, Dict
from enum import Enum
from adb_shell.adb_device import AdbDeviceTcp, AdbDeviceUsb
from adb_shell.auth.sign_pythonrsa import PythonRSASigner


class DeviceMode(Enum):
    """Supported device connection modes"""
    UNKNOWN = 0
    ADB = 1
    FASTBOOT = 2
    MTK_PRELOADER = 3
    MTK_DOWNLOAD = 4
    OFFLINE = 5


class DeviceInterface:
    """Main device communication interface"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.device = None
        self.mode = DeviceMode.UNKNOWN
        self.device_info = {}
        
    def detect_device(self) -> bool:
        """
        Detect connected device and its mode
        Returns True if device found
        """
        self.logger.info("Scanning for connected devices...")
        
        # Try ADB first
        if self._detect_adb():
            self.mode = DeviceMode.ADB
            return True
        
        # Try MTK USB modes
        if self._detect_mtk_device():
            return True
            
        # Try Fastboot
        if self._detect_fastboot():
            self.mode = DeviceMode.FASTBOOT
            return True
        
        self.mode = DeviceMode.OFFLINE
        return False
    
    def _detect_adb(self) -> bool:
        """Detect device in ADB mode"""
        try:
            self.logger.info("Checking for ADB devices...")
            import subprocess
            from pathlib import Path
            
            # Try local ADB first (auto-installed)
            base_dir = Path(__file__).parent.parent
            local_adb = base_dir / "tools" / "platform-tools" / "adb.exe"
            
            if local_adb.exists():
                adb_cmd = str(local_adb)
            else:
                # Fallback to system ADB
                adb_cmd = 'adb'
            
            # Run adb devices command
            result = subprocess.run(
                [adb_cmd, 'devices'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                # Skip header line "List of devices attached"
                for line in lines[1:]:
                    if line.strip() and '\tdevice' in line:
                        # Found a connected device
                        device_serial = line.split('\t')[0]
                        self.logger.info(f"Found ADB device: {device_serial}")
                        self.device_info['serial'] = device_serial
                        self.device_info['adb_available'] = True
                        return True
                    if line.strip() and ('\tunauthorized' in line or '\toffline' in line):
                        device_serial = line.split('\t')[0]
                        self.logger.info(f"ADB device present but not authorized: {device_serial}")
                        self.device_info['serial'] = device_serial
                        self.device_info['adb_available'] = True
                        self.device_info['adb_state'] = line.split('\t')[1]
                        return True
            
            return False
        except FileNotFoundError:
            # This shouldn't happen with auto-installer, but just in case
            self.logger.warning("ADB not found. Auto-installer may have failed.")
            return False
        except Exception as e:
            self.logger.debug(f"ADB detection failed: {e}")
            return False
    
    def _detect_mtk_device(self) -> bool:
        """Detect MediaTek device via USB"""
        try:
            vendor_id = int(self.config.get('mtk.vendor_id'), 16)
            product_ids = [int(pid, 16) for pid in self.config.get('mtk.product_ids')]
            
            for product_id in product_ids:
                dev = usb.core.find(idVendor=vendor_id, idProduct=product_id)
                if dev is not None:
                    self.device = dev
                    self.logger.info(f"Found MTK device: VID={vendor_id:04x}, PID={product_id:04x}")
                    
                    # Determine mode by product ID
                    if product_id == 0x0003:
                        self.mode = DeviceMode.MTK_PRELOADER
                    elif product_id in [0x2000, 0x201c]:
                        self.mode = DeviceMode.MTK_DOWNLOAD
                    
                    return True
        except Exception as e:
            self.logger.debug(f"MTK USB detection failed: {e}")
            return False
        
        return False
    
    def _detect_fastboot(self) -> bool:
        """Detect device in Fastboot mode"""
        try:
            # TODO: Implement Fastboot detection
            self.logger.info("Checking for Fastboot devices...")
            return False
        except Exception as e:
            self.logger.debug(f"Fastboot detection failed: {e}")
            return False
    
    def get_device_info(self) -> Dict:
        """Retrieve comprehensive device information"""
        if self.mode == DeviceMode.UNKNOWN or self.mode == DeviceMode.OFFLINE:
            return {}
        
        info = {
            'mode': self.mode.name,
            'connected': True
        }
        
        if self.mode == DeviceMode.ADB:
            info.update(self._get_adb_info())
        elif self.mode in [DeviceMode.MTK_PRELOADER, DeviceMode.MTK_DOWNLOAD]:
            info.update(self._get_mtk_info())
        
        self.device_info = info
        return info
    
    def _get_adb_info(self) -> Dict:
        """Get device info via ADB"""
        return {
            'manufacturer': 'Unknown',
            'model': 'Unknown',
            'android_version': 'Unknown',
            'build_number': 'Unknown'
        }
    
    def _get_mtk_info(self) -> Dict:
        """Get MediaTek device info via USB"""
        return {
            'chip': self._detect_mtk_chip(),
            'preloader_version': 'Unknown',
            'emmc_size': 'Unknown'
        }
    
    def _detect_mtk_chip(self) -> str:
        """Detect MediaTek chip model"""
        # This would require actual MTK protocol implementation
        return "MT6580"  # Placeholder
    
    def send_mtk_command(self, command: bytes) -> bytes:
        """
        Send command to MTK device in preloader/download mode
        """
        if self.device is None:
            raise Exception("No device connected")
        
        if self.mode not in [DeviceMode.MTK_PRELOADER, DeviceMode.MTK_DOWNLOAD]:
            raise Exception("Device not in MTK mode")
        
        try:
            # Get endpoint
            cfg = self.device.get_active_configuration()
            intf = cfg[(0, 0)]
            
            ep_out = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
            )
            
            ep_in = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
            )
            
            # Send command
            ep_out.write(command)
            
            # Read response
            response = ep_in.read(512, timeout=5000)
            return bytes(response)
            
        except Exception as e:
            self.logger.error(f"MTK command failed: {e}")
            raise
    
    def reboot_to_mode(self, target_mode: DeviceMode) -> bool:
        """Reboot device to specified mode"""
        if self.mode == DeviceMode.ADB:
            if target_mode == DeviceMode.FASTBOOT:
                return self._adb_reboot_fastboot()
            elif target_mode == DeviceMode.MTK_DOWNLOAD:
                return self._adb_reboot_download()
        
        return False
    
    def _adb_reboot_fastboot(self) -> bool:
        """Reboot to fastboot via ADB"""
        # TODO: Implement
        return False
    
    def _adb_reboot_download(self) -> bool:
        """Reboot to MTK download mode via ADB"""
        # TODO: Implement
        return False
    
    def disconnect(self):
        """Safely disconnect from device"""
        if self.device:
            try:
                usb.util.dispose_resources(self.device)
            except:
                pass
        self.device = None
        self.mode = DeviceMode.UNKNOWN
