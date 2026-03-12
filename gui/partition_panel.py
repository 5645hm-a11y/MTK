"""
Partition Panel - Shows list of device partitions
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QGroupBox, QHeaderView, QProgressBar
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor
from typing import List
from core.partition_extractor import PartitionInfo
from utils.i18n import get_i18n


class PartitionPanel(QWidget):
    """Panel displaying partition list and status"""
    
    partition_selected = pyqtSignal(str)
    
    def __init__(self, config):
        super().__init__()
        
        self.config = config
        self.i18n = get_i18n()
        self.partitions = []
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI elements"""
        layout = QVBoxLayout(self)
        
        # Partition table
        partition_group = QGroupBox(self.i18n.t('partition_panel.title'))
        partition_layout = QVBoxLayout()
        
        self.partition_table = QTableWidget()
        self.partition_table.setColumnCount(4)
        self.partition_table.setHorizontalHeaderLabels([
            self.i18n.t('partition_panel.name'),
            self.i18n.t('partition_panel.size_mb'),
            self.i18n.t('partition_panel.type'),
            self.i18n.t('partition_panel.status')
        ])
        
        # Configure table
        header = self.partition_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.partition_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        partition_layout.addWidget(self.partition_table)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        partition_layout.addWidget(self.progress_bar)
        
        partition_group.setLayout(partition_layout)
        layout.addWidget(partition_group)
    
    def load_partitions(self, partitions: List[PartitionInfo]):
        """Load partition list into table"""
        self.partitions = partitions
        self.partition_table.setRowCount(len(partitions))
        
        for idx, partition in enumerate(partitions):
            # Name
            name_item = QTableWidgetItem(partition.name)
            self.partition_table.setItem(idx, 0, name_item)
            
            # Size in MB
            size_mb = partition.size / (1024 * 1024)
            size_item = QTableWidgetItem(f"{size_mb:.2f}")
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.partition_table.setItem(idx, 1, size_item)
            
            # Type
            type_item = QTableWidgetItem(partition.type)
            self.partition_table.setItem(idx, 2, type_item)
            
            # Status
            status_item = QTableWidgetItem(self.i18n.t('partition_panel.ready'))
            self.partition_table.setItem(idx, 3, status_item)

    def update_partition_status(self, partition_name: str, status: str, error_text: str = ""):
        """Update one partition status and color in table."""
        target_row = None
        for row in range(self.partition_table.rowCount()):
            item = self.partition_table.item(row, 0)
            if item and item.text() == partition_name:
                target_row = row
                break

        if target_row is None:
            return

        status_item = self.partition_table.item(target_row, 3)
        if status_item is None:
            status_item = QTableWidgetItem()
            self.partition_table.setItem(target_row, 3, status_item)

        if status == 'extracting':
            status_item.setText("Extracting...")
            status_item.setForeground(QColor(255, 170, 0))
        elif status == 'success':
            status_item.setText("Extracted")
            status_item.setForeground(QColor(0, 170, 0))
        elif status == 'failed':
            status_item.setText("Failed")
            status_item.setForeground(QColor(220, 50, 50))
            if error_text:
                status_item.setToolTip(error_text)
    
    def on_selection_changed(self):
        """Handle partition selection"""
        selected_items = self.partition_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            partition_name = self.partition_table.item(row, 0).text()
            self.partition_selected.emit(partition_name)
    
    def update_extraction_progress(self, partition_name: str, current: int, total: int):
        """Update extraction progress for a partition"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(100)
        percent = int((current / total) * 100) if total > 0 else 0
        if percent < 0:
            percent = 0
        if percent > 100:
            percent = 100
        self.progress_bar.setValue(percent)
        self.progress_bar.setFormat(f"{partition_name}: {percent}%")
        
        if current >= total:
            self.progress_bar.setVisible(False)
