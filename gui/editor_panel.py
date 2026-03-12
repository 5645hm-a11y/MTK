"""
Editor Panel - Interface for editing firmware partitions
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTextEdit, QFileDialog,
    QGroupBox, QListWidget, QMessageBox
)
from PyQt6.QtCore import pyqtSignal
from pathlib import Path
from utils.i18n import get_i18n


class EditorPanel(QWidget):
    """Panel for editing firmware components"""
    
    modification_made = pyqtSignal(dict)
    
    def __init__(self, firmware_editor, config):
        super().__init__()
        
        self.editor = firmware_editor
        self.config = config
        self.i18n = get_i18n()
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI elements"""
        layout = QVBoxLayout(self)
        
        # Boot Logo Editor
        logo_group = QGroupBox(self.i18n.t('editor_panel.boot_logo_section'))
        logo_layout = QVBoxLayout()
        
        logo_btn_layout = QHBoxLayout()
        self.logo_path_edit = QLineEdit()
        self.logo_path_edit.setPlaceholderText(self.i18n.t('editor_panel.logo_placeholder'))
        self.logo_path_edit.setReadOnly(True)
        
        browse_logo_btn = QPushButton(self.i18n.t('editor_panel.browse'))
        browse_logo_btn.clicked.connect(self.browse_logo)
        
        apply_logo_btn = QPushButton(self.i18n.t('editor_panel.apply_logo'))
        apply_logo_btn.clicked.connect(self.apply_logo)
        
        logo_btn_layout.addWidget(self.logo_path_edit)
        logo_btn_layout.addWidget(browse_logo_btn)
        logo_btn_layout.addWidget(apply_logo_btn)
        
        logo_layout.addLayout(logo_btn_layout)
        logo_group.setLayout(logo_layout)
        layout.addWidget(logo_group)
        
        # Build Properties Editor
        props_group = QGroupBox(self.i18n.t('editor_panel.build_props_section'))
        props_layout = QVBoxLayout()
        
        props_layout.addWidget(QLabel(self.i18n.t('editor_panel.build_props_section') + ":"))
        
        self.props_edit = QTextEdit()
        self.props_edit.setPlaceholderText(self.i18n.t('editor_panel.props_placeholder'))
        props_layout.addWidget(self.props_edit)
        
        apply_props_btn = QPushButton(self.i18n.t('editor_panel.apply_properties'))
        apply_props_btn.clicked.connect(self.apply_properties)
        props_layout.addWidget(apply_props_btn)
        
        props_group.setLayout(props_layout)
        layout.addWidget(props_group)
        
        # Changes Log
        changes_group = QGroupBox(self.i18n.t('editor_panel.changes_log'))
        changes_layout = QVBoxLayout()
        
        self.changes_list = QListWidget()
        changes_layout.addWidget(self.changes_list)
        
        clear_btn = QPushButton(self.i18n.t('editor_panel.clear_changes'))
        clear_btn.clicked.connect(self.clear_changes)
        changes_layout.addWidget(clear_btn)
        
        changes_group.setLayout(changes_layout)
        layout.addWidget(changes_group)
    
    def browse_logo(self):
        """Browse for boot logo image"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.i18n.t('messages.select_logo'),
            "",
            "Images (*.png *.jpg *.bmp)"
        )
        
        if file_path:
            self.logo_path_edit.setText(file_path)
    
    def apply_logo(self):
        """Apply new boot logo"""
        logo_path = self.logo_path_edit.text()
        if not logo_path:
            QMessageBox.warning(self, self.i18n.t('messages.error'), self.i18n.t('messages.no_logo'))
            return
        
        try:
            if self.editor.modify_boot_logo(Path(logo_path)):
                self.changes_list.addItem(f"Boot logo replaced: {logo_path}")
                self.modification_made.emit({
                    'type': 'boot_logo',
                    'file': logo_path
                })
                QMessageBox.information(self, self.i18n.t('messages.success'), self.i18n.t('messages.logo_applied'))
            else:
                QMessageBox.warning(self, self.i18n.t('messages.error'), self.i18n.t('messages.logo_failed'))
        except Exception as e:
            QMessageBox.critical(self, self.i18n.t('messages.error'), f"Failed to apply logo: {e}")
    
    def apply_properties(self):
        """Apply build.prop modifications"""
        props_text = self.props_edit.toPlainText().strip()
        if not props_text:
            QMessageBox.warning(self, self.i18n.t('messages.error'), self.i18n.t('messages.no_props'))
            return
        
        # Parse properties
        properties = {}
        for line in props_text.split('\n'):
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                properties[key.strip()] = value.strip()
        
        if not properties:
            QMessageBox.warning(self, self.i18n.t('messages.error'), self.i18n.t('messages.no_valid_props'))
            return
        
        try:
            if self.editor.modify_build_prop(properties):
                for key, value in properties.items():
                    self.changes_list.addItem(f"Property: {key} = {value}")
                self.modification_made.emit({
                    'type': 'build_prop',
                    'properties': properties
                })
                QMessageBox.information(self, self.i18n.t('messages.success'), self.i18n.t('messages.props_applied'))
            else:
                QMessageBox.warning(self, self.i18n.t('messages.error'), self.i18n.t('messages.props_failed'))
        except Exception as e:
            QMessageBox.critical(self, self.i18n.t('messages.error'), f"Failed to apply properties: {e}")
    
    def clear_changes(self):
        """Clear changes list"""
        self.changes_list.clear()
