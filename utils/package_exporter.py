"""
Package Exporter
Creates flashable firmware packages
"""

import logging
import zipfile
import shutil
from pathlib import Path
from typing import Dict, List
import hashlib
from datetime import datetime


class PackageExporter:
    """Export modified firmware as flashable package"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def create_flash_package(self, 
                            partitions: Dict[str, Path],
                            scatter_file: Path,
                            output_path: Path,
                            include_tools: bool = True) -> Path:
        """
        Create complete flashable package
        
        Args:
            partitions: Dictionary of partition files
            scatter_file: Scatter file path
            output_path: Output directory or ZIP file path
            include_tools: Whether to include SP Flash Tool
        
        Returns:
            Path to created package
        """
        self.logger.info("Creating flashable firmware package...")
        
        # Determine output format
        if output_path.suffix.lower() == '.zip':
            return self._create_zip_package(
                partitions, scatter_file, output_path, include_tools
            )
        else:
            return self._create_directory_package(
                partitions, scatter_file, output_path, include_tools
            )
    
    def _create_directory_package(self,
                                  partitions: Dict[str, Path],
                                  scatter_file: Path,
                                  output_dir: Path,
                                  include_tools: bool) -> Path:
        """Create firmware package in directory structure"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectory for firmware
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        package_dir = output_dir / f"firmware_package_{timestamp}"
        package_dir.mkdir(exist_ok=True)
        
        # Copy partitions
        self.logger.info("Copying partition images...")
        for name, path in partitions.items():
            if path and path.exists():
                dest = package_dir / path.name
                shutil.copy(path, dest)
                self.logger.debug(f"Copied {name}: {path.name}")
        
        # Copy scatter file
        if scatter_file and scatter_file.exists():
            dest_scatter = package_dir / scatter_file.name
            shutil.copy(scatter_file, dest_scatter)
            self.logger.info(f"Copied scatter file: {scatter_file.name}")
        
        # Create checksums file
        self._create_checksums_file(package_dir)
        
        # Create README
        self._create_readme(package_dir)
        
        # Create flash instructions
        self._create_flash_instructions(package_dir)
        
        self.logger.info(f"Package created: {package_dir}")
        return package_dir
    
    def _create_zip_package(self,
                           partitions: Dict[str, Path],
                           scatter_file: Path,
                           output_zip: Path,
                           include_tools: bool) -> Path:
        """Create firmware package as ZIP file"""
        self.logger.info(f"Creating ZIP package: {output_zip}")
        
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add partitions
            for name, path in partitions.items():
                if path and path.exists():
                    zf.write(path, path.name)
                    self.logger.debug(f"Added to ZIP: {path.name}")
            
            # Add scatter file
            if scatter_file and scatter_file.exists():
                zf.write(scatter_file, scatter_file.name)
            
            # Add README
            readme_content = self._generate_readme_content()
            zf.writestr("README.txt", readme_content)
            
            # Add flash instructions
            instructions = self._generate_flash_instructions()
            zf.writestr("FLASH_INSTRUCTIONS.txt", instructions)
        
        self.logger.info(f"ZIP package created: {output_zip}")
        return output_zip
    
    def _create_checksums_file(self, package_dir: Path):
        """Create MD5 checksums file"""
        checksums_file = package_dir / "checksums.md5"
        
        with open(checksums_file, 'w') as f:
            for file_path in sorted(package_dir.glob("*.img")):
                md5_hash = self._compute_md5(file_path)
                f.write(f"{md5_hash}  {file_path.name}\n")
        
        self.logger.info("Created checksums file")
    
    def _compute_md5(self, file_path: Path) -> str:
        """Compute MD5 checksum"""
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                md5.update(chunk)
        return md5.hexdigest()
    
    def _create_readme(self, package_dir: Path):
        """Create README file"""
        content = self._generate_readme_content()
        readme_file = package_dir / "README.txt"
        
        with open(readme_file, 'w') as f:
            f.write(content)
    
    def _generate_readme_content(self) -> str:
        """Generate README content"""
        return f"""
MTK FIRMWARE PACKAGE
====================

Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Tool: MTK Firmware Editor Pro v1.0.0

CONTENTS
--------
This package contains modified Android firmware for MediaTek devices.

IMPORTANT WARNINGS
-----------------
⚠️ Flashing firmware carries risks including:
   - Permanent device damage (bricking)
   - Loss of warranty
   - Data loss

⚠️ Only flash this firmware if:
   - You know what you're doing
   - This firmware is compatible with your device
   - You have a backup plan (original firmware backup)

⚠️ The creators of this package are NOT responsible for any damage.

REQUIREMENTS
-----------
- SP Flash Tool (latest version recommended)
- USB drivers for your device
- Device in download mode or powered off
- Battery charged above 50%

See FLASH_INSTRUCTIONS.txt for detailed flashing steps.

VERIFICATION
-----------
Check MD5 checksums before flashing (see checksums.md5).

SUPPORT
-------
This is custom firmware. No official support is provided.
"""
    
    def _create_flash_instructions(self, package_dir: Path):
        """Create flash instructions file"""
        content = self._generate_flash_instructions()
        instructions_file = package_dir / "FLASH_INSTRUCTIONS.txt"
        
        with open(instructions_file, 'w') as f:
            f.write(content)
    
    def _generate_flash_instructions(self) -> str:
        """Generate flashing instructions"""
        return """
FLASHING INSTRUCTIONS
====================

PREPARATION
-----------
1. Install MTK USB drivers on your PC
2. Download and extract SP Flash Tool
3. Charge device battery to at least 50%
4. Backup all important data from device
5. Extract this firmware package to a folder

FLASHING STEPS
--------------
1. Open SP Flash Tool
   
2. Load Scatter File
   - Click "Scatter-loading" or "Download-Agent"
   - Browse and select the scatter file (MT*_scatter.txt)
   
3. Verify Partition Files
   - Check that all partition files are found
   - Green checkmarks should appear
   
4. Select Download Mode
   - Choose "Download Only" (recommended for full flash)
   - OR "Firmware Upgrade" (for incremental update)
   
5. Connect Device
   - Power off your device completely
   - Click "Download" button in SP Flash Tool
   - Connect device to PC via USB
   - Device should automatically enter download mode
   
6. Wait for Completion
   - Do NOT disconnect during flashing
   - Wait for green success circle
   
7. Disconnect and Boot
   - Disconnect USB cable
   - Power on device
   - First boot may take 5-10 minutes

TROUBLESHOOTING
---------------
Problem: Device not detected
Solution: Install proper USB drivers, try different USB port

Problem: Red error in SP Flash Tool
Solution: Re-download firmware, verify scatter file, check USB cable

Problem: Device won't boot after flash
Solution: Re-flash firmware, or restore original firmware backup

Problem: Boot loop
Solution: Perform factory reset from recovery mode

IMPORTANT NOTES
---------------
- Do NOT remove battery during flashing
- Do NOT disconnect USB cable during flashing
- Use original USB cable if possible
- First boot after flash takes longer than usual
- Some functions may require additional configuration

For advanced users: You can selectively flash specific partitions
by unchecking unwanted partitions before clicking Download.
"""
