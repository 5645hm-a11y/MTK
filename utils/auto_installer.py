"""
Auto Installer - Downloads and installs required tools automatically
"""

import os
import sys
import zipfile
import urllib.request
import logging
from pathlib import Path
from typing import Optional


class AutoInstaller:
    """Automatically downloads and installs required tools"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_dir = Path(__file__).parent.parent
        self.tools_dir = self.base_dir / "tools"
        self.tools_dir.mkdir(exist_ok=True)
        
    def ensure_adb(self) -> Optional[str]:
        """
        Ensure ADB is available, download if needed
        Returns path to adb executable or None if failed
        """
        # Check if already downloaded
        adb_path = self.tools_dir / "platform-tools" / "adb.exe"
        
        if adb_path.exists():
            self.logger.info(f"ADB found at: {adb_path}")
            return str(adb_path)
        
        # Download ADB Platform Tools
        self.logger.info("ADB not found. Downloading Android Platform Tools...")
        
        try:
            # Download URL for Windows Platform Tools
            url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
            zip_path = self.tools_dir / "platform-tools.zip"
            
            # Download with progress
            self._download_file(url, zip_path)
            
            # Extract
            self.logger.info("Extracting Platform Tools...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.tools_dir)
            
            # Cleanup
            zip_path.unlink()
            
            if adb_path.exists():
                self.logger.info("ADB installed successfully!")
                return str(adb_path)
            else:
                self.logger.error("ADB installation failed - executable not found")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to download/install ADB: {e}")
            return None
    
    def ensure_fastboot(self) -> Optional[str]:
        """
        Ensure Fastboot is available (comes with platform-tools)
        Returns path to fastboot executable or None if failed
        """
        # Fastboot comes with platform-tools
        self.ensure_adb()
        
        fastboot_path = self.tools_dir / "platform-tools" / "fastboot.exe"
        
        if fastboot_path.exists():
            self.logger.info(f"Fastboot found at: {fastboot_path}")
            return str(fastboot_path)
        
        return None
    
    def _download_file(self, url: str, destination: Path, chunk_size: int = 8192):
        """Download file with progress"""
        try:
            with urllib.request.urlopen(url) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                
                with open(destination, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            self.logger.info(f"Download progress: {progress:.1f}%")
                
                self.logger.info(f"Download complete: {destination}")
                
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            raise
    
    def check_winusb_driver(self) -> bool:
        """
        Check if WinUSB/LibUSB drivers are available
        Note: This cannot be auto-installed, requires Zadig
        """
        try:
            import usb.core
            # Try to find any USB device to test if backend works
            devices = list(usb.core.find(find_all=True))
            return True
        except Exception as e:
            self.logger.warning(f"USB backend not available: {e}")
            return False
    
    def install_all(self):
        """Install all required tools"""
        self.logger.info("=" * 60)
        self.logger.info("Installing required tools...")
        self.logger.info("=" * 60)
        
        # Install ADB/Fastboot
        adb_path = self.ensure_adb()
        if adb_path:
            self.logger.info(f"✓ ADB installed: {adb_path}")
        else:
            self.logger.warning("✗ ADB installation failed")
        
        fastboot_path = self.ensure_fastboot()
        if fastboot_path:
            self.logger.info(f"✓ Fastboot installed: {fastboot_path}")
        else:
            self.logger.warning("✗ Fastboot installation failed")
        
        # Check USB drivers
        if self.check_winusb_driver():
            self.logger.info("✓ USB drivers available")
        else:
            self.logger.warning("✗ USB drivers not available (install Zadig for bricked devices)")
        
        self.logger.info("=" * 60)


def get_installer():
    """Get singleton installer instance"""
    if not hasattr(get_installer, '_instance'):
        get_installer._instance = AutoInstaller()
    return get_installer._instance
