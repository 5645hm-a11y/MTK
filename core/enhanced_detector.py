"""
Enhanced Device Detection Module
Supports detection of powered-off and bricked MTK devices
"""

import logging
import time
from typing import Optional, List, Dict, Tuple
from enum import Enum
import subprocess
import re
import json


class DeviceState(Enum):
    """Extended device states"""
    POWERED_ON = "Powered On"
    POWERED_OFF = "Powered Off"
    BRICK = "Brick/Recovery"
    PRELOADER = "Preloader"
    DOWNLOAD_MODE = "Download Mode"
    UNKNOWN = "Unknown"


class EnhancedDeviceDetector:
    """Enhanced device detection for all MTK states"""
    
    MTK_VENDOR_ID = "0e8d"
    
    # MTK Product IDs for different modes
    MTK_PRELOADER_PIDS = ["0003"]
    MTK_DOWNLOAD_PIDS = ["2000", "201c", "0003"]
    MTK_NORMAL_PIDS = ["2008"]  # Normal USB connection
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def detect_all_modes(self) -> List[Dict]:
        """Detect devices in all possible modes"""
        detected_devices = []
        
        # Method 1: Windows Device Manager check
        wmi_devices = self._check_windows_devices()
        detected_devices.extend(wmi_devices)
        
        # Method 2: USB VID/PID scan
        usb_devices = self._scan_usb_devices()
        detected_devices.extend(usb_devices)
        
        # Method 3: ADB check
        adb_devices = self._check_adb_devices()
        detected_devices.extend(adb_devices)

        # Method 4: Generic Android interface check (works without adb.exe)
        generic_android_devices = self._check_generic_android_interfaces()
        detected_devices.extend(generic_android_devices)
        
        return detected_devices

    def _check_generic_android_interfaces(self) -> List[Dict]:
        """Detect powered-on Android devices using Windows interface names."""
        devices = []

        try:
            cmd = [
                'powershell',
                '-Command',
                "Get-PnpDevice | Where-Object {$_.FriendlyName -match 'Android|ADB|MTP|Composite' -or $_.InstanceId -match 'USB\\\\VID_'} | Select-Object FriendlyName, InstanceId, Status | Format-List"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=8
            )

            if result.returncode == 0:
                current_device = {}
                for raw_line in result.stdout.split('\n'):
                    line = raw_line.strip()

                    if ':' in line:
                        key, value = line.split(':', 1)
                        current_device[key.strip()] = value.strip()

                    if not line and current_device:
                        name = current_device.get('FriendlyName', '')
                        instance_id = current_device.get('InstanceId', '')
                        status = current_device.get('Status', 'Unknown')

                        android_hint = any(
                            token in (name + ' ' + instance_id).lower()
                            for token in ['android', 'adb', 'mtp', 'composite']
                        )

                        if android_hint and status.lower() in ('ok', 'unknown'):
                            devices.append({
                                'method': 'windows_android_interface',
                                'state': DeviceState.POWERED_ON,
                                'friendly_name': name or 'Android Device',
                                'instance_id': instance_id,
                                'status': status
                            })
                            self.logger.info(f"Found Android interface via WDM: {name}")

                        current_device = {}

        except Exception as e:
            self.logger.debug(f"Generic Android interface check failed: {e}")

        return devices
    
    def _check_windows_devices(self) -> List[Dict]:
        """Check Windows Device Manager for MTK devices"""
        devices = []
        
        try:
            # Use PowerShell and JSON output for robust parsing
            cmd = [
                'powershell',
                '-Command',
                f"Get-PnpDevice -PresentOnly | Where-Object {{$_.InstanceId -like '*VID_{self.MTK_VENDOR_ID.upper()}*'}} | Select-Object FriendlyName, InstanceId, Status | ConvertTo-Json -Compress"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                parsed = json.loads(result.stdout)
                entries = parsed if isinstance(parsed, list) else [parsed]

                for entry in entries:
                    instance_id = str(entry.get('InstanceId', ''))
                    friendly_name = str(entry.get('FriendlyName', 'MTK Device'))

                    vid_match = re.search(r'VID_([0-9A-F]{4})', instance_id, re.IGNORECASE)
                    pid_match = re.search(r'PID_([0-9A-F]{4})', instance_id, re.IGNORECASE)

                    if vid_match and pid_match:
                        vid = vid_match.group(1).lower()
                        pid = pid_match.group(1).lower()

                        device_info = {
                            'method': 'windows_device_manager',
                            'vid': vid,
                            'pid': pid,
                            'state': self._determine_state_by_pid(pid),
                            'friendly_name': friendly_name,
                            'status': str(entry.get('Status', 'Unknown'))
                        }
                        devices.append(device_info)
                        self.logger.info(f"Found MTK device via WDM: VID={vid}, PID={pid}, Name={friendly_name}")
        
        except Exception as e:
            self.logger.debug(f"Windows device check failed: {e}")
        
        return devices
    
    def _scan_usb_devices(self) -> List[Dict]:
        """Scan USB devices using system commands"""
        devices = []
        
        try:
            # Use PowerShell Get-PnpDevice with JSON output
            cmd = [
                'powershell',
                '-Command',
                "Get-PnpDevice -PresentOnly -Class Ports,USB | Select-Object InstanceId, FriendlyName, Status | ConvertTo-Json -Compress"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                parsed = json.loads(result.stdout)
                entries = parsed if isinstance(parsed, list) else [parsed]

                for entry in entries:
                    instance_id = str(entry.get('InstanceId', ''))
                    if f'VID_{self.MTK_VENDOR_ID.upper()}' in instance_id.upper():
                        pid_match = re.search(r'PID_([0-9A-F]{4})', instance_id, re.IGNORECASE)
                        if pid_match:
                            pid = pid_match.group(1).lower()
                            device_info = {
                                'method': 'usb_scan',
                                'vid': self.MTK_VENDOR_ID,
                                'pid': pid,
                                'state': self._determine_state_by_pid(pid),
                                'friendly_name': str(entry.get('FriendlyName', 'Unknown')),
                                'status': str(entry.get('Status', 'Unknown'))
                            }
                            devices.append(device_info)
                            self.logger.info(f"Found MTK via USB scan: PID={pid}, Status={device_info['status']}")
        
        except Exception as e:
            self.logger.debug(f"USB scan failed: {e}")
        
        return devices
    
    def _check_adb_devices(self) -> List[Dict]:
        """Check for devices via ADB"""
        devices = []
        
        try:
            from pathlib import Path
            
            # Try local ADB first
            base_dir = Path(__file__).parent.parent
            local_adb = base_dir / "tools" / "platform-tools" / "adb.exe"
            
            if local_adb.exists():
                adb_cmd = str(local_adb)
            else:
                adb_cmd = 'adb'
            
            result = subprocess.run(
                [adb_cmd, 'devices', '-l'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip() and 'device' in line.lower():
                        device_info = {
                            'method': 'adb',
                            'state': DeviceState.POWERED_ON,
                            'details': line.strip()
                        }
                        devices.append(device_info)
                        self.logger.info(f"Found device via ADB: {line.strip()}")
        
        except FileNotFoundError:
            self.logger.debug("ADB not found in PATH")
        except Exception as e:
            self.logger.debug(f"ADB check failed: {e}")
        
        return devices
    
    def _determine_state_by_pid(self, pid: str) -> DeviceState:
        """Determine device state based on PID"""
        pid = pid.lower()
        
        if pid in self.MTK_PRELOADER_PIDS:
            return DeviceState.PRELOADER
        elif pid in self.MTK_DOWNLOAD_PIDS:
            return DeviceState.DOWNLOAD_MODE
        elif pid in self.MTK_NORMAL_PIDS:
            return DeviceState.POWERED_ON
        else:
            # Unknown PID might be brick or special mode
            return DeviceState.BRICK
    
    def _extract_friendly_name(self, line: str) -> str:
        """Extract friendly name from device line"""
        # Simple extraction, can be improved
        parts = line.split()
        if parts:
            return ' '.join(parts[:3])
        return "MTK Device"
    
    def get_best_device(self) -> Optional[Dict]:
        """Get the best available device"""
        all_devices = self.detect_all_modes()
        
        if not all_devices:
            return None
        
        # Prioritize: Powered On > Download Mode > Preloader > Brick
        priority_order = [
            DeviceState.POWERED_ON,
            DeviceState.DOWNLOAD_MODE,
            DeviceState.PRELOADER,
            DeviceState.BRICK
        ]
        
        for state in priority_order:
            for device in all_devices:
                if device.get('state') == state:
                    return device
        
        # Return first device if no priority match
        return all_devices[0]
    
    def check_for_brick_recovery(self) -> bool:
        """
        Check if device is in brick/recovery state
        Looks for MTK devices even when in error state
        """
        try:
            cmd = [
                'powershell',
                '-Command',
                f"Get-PnpDevice | Where-Object {{$_.InstanceId -like '*VID_{self.MTK_VENDOR_ID.upper()}*' -and ($_.Status -eq 'Error' -or $_.Status -eq 'Unknown')}} | Measure-Object"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=5
            )
            
            if result.returncode == 0:
                # Check if count > 0
                if 'Count' in result.stdout:
                    match = re.search(r'Count\s*:\s*(\d+)', result.stdout)
                    if match and int(match.group(1)) > 0:
                        self.logger.info("Detected MTK device in error/brick state")
                        return True
        
        except Exception as e:
            self.logger.debug(f"Brick check failed: {e}")
        
        return False
