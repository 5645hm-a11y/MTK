"""
MTK Firmware Editor Pro
Advanced Android Firmware Modification Tool for MediaTek Devices

This application allows:
- Connecting to MTK devices (even in non-bootable state)
- Extracting firmware partitions
- Editing firmware in real-time
- Generating Scatter files for SP Flash Tool
- Live preview of modifications
- Comprehensive testing framework
"""

import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from gui.main_window import MainWindow
from core.config_manager import ConfigManager
from utils.logger import setup_logger
from utils.i18n import get_i18n


def main():
    """Main application entry point"""
    
    # Setup logging
    logger = setup_logger()
    logger.info("Starting MTK Firmware Editor Pro")
    
    # Auto-install required tools (ADB, Fastboot)
    logger.info("Checking and installing required tools...")
    from utils.auto_installer import get_installer
    installer = get_installer()
    installer.install_all()
    
    # Load configuration
    config = ConfigManager()
    
    # Initialize i18n
    i18n = get_i18n()
    default_lang = config.get('application.language', 'en')
    i18n.set_language(default_lang)
    logger.info(f"Language set to: {i18n.get_language_name()}")
    
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName(config.get('application.name'))
    app.setApplicationVersion(config.get('application.version'))
    
    # Apply dark theme
    app.setStyle('Fusion')
    
    # Create and show main window
    window = MainWindow(config)
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
