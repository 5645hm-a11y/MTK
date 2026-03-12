"""
Device Panel - Shows device connection status and information
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QGroupBox, QGridLayout
)
from PyQt6.QtCore import pyqtSignal
from utils.i18n import get_i18n


class DevicePanel(QWidget):
    """Panel displaying device connection status"""
    
    device_detected = pyqtSignal(dict)
    
    def __init__(self, device_interface, config):
        super().__init__()
        
        self.device = device_interface
        self.config = config
        self.i18n = get_i18n()
        self.connected = False
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI elements"""
        layout = QVBoxLayout(self)
        
        # Device info group
        device_group = QGroupBox(self.i18n.t('device_panel.title'))
        device_layout = QGridLayout()
        
        # Status
        device_layout.addWidget(QLabel(f"{self.i18n.t('device_panel.status')}:"), 0, 0)
        self.status_label = QLabel(self.i18n.t('device_panel.not_connected'))
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        device_layout.addWidget(self.status_label, 0, 1)
        
        # Mode
        device_layout.addWidget(QLabel(f"{self.i18n.t('device_panel.mode')}:"), 1, 0)
        self.mode_label = QLabel("N/A")
        device_layout.addWidget(self.mode_label, 1, 1)
        
        # Chip
        device_layout.addWidget(QLabel(f"{self.i18n.t('device_panel.chip')}:"), 2, 0)
        self.chip_label = QLabel("N/A")
        device_layout.addWidget(self.chip_label, 2, 1)
        
        # Model
        device_layout.addWidget(QLabel(f"{self.i18n.t('device_panel.model')}:"), 3, 0)
        self.model_label = QLabel("N/A")
        device_layout.addWidget(self.model_label, 3, 1)
        
        device_group.setLayout(device_layout)
        layout.addWidget(device_group)
        
        # Connection button
        self.connect_btn = QPushButton(self.i18n.t('device_panel.connect_button'))
        self.connect_btn.clicked.connect(self.detect_device)
        layout.addWidget(self.connect_btn)
        
        layout.addStretch()
    
    def detect_device(self):
        """Trigger device detection"""
        if self.device.detect_device():
            info = self.device.get_device_info()
            self.update_device_info(info)
    
    def update_device_info(self, info: dict):
        """Update displayed device information"""
        if not info or not info.get('connected', False):
            self.status_label.setText(self.i18n.t('device_panel.not_connected'))
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.mode_label.setText("N/A")
            self.chip_label.setText("N/A")
            self.model_label.setText("N/A")
            self.connected = False
            return
        
        self.connected = True
        self.status_label.setText(self.i18n.t('device_panel.connected'))
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        
        self.mode_label.setText(info.get('mode', 'Unknown'))
        self.chip_label.setText(info.get('chip', 'Unknown'))
        self.model_label.setText(info.get('model', 'Unknown'))
        
        self.device_detected.emit(info)
    
    def is_connected(self) -> bool:
        """Check if device is connected"""
        return self.connected
