"""
Preview Panel - Live preview of Android device screen with modifications
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QGroupBox, QMessageBox, QDialog,
    QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPolygon
from PyQt6.QtCore import QPoint
from PIL import Image
import io
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from utils.i18n import get_i18n
from core.partition_flasher import PartitionFlasher
from core.android_emulator import AndroidEmulator


class FlashingThread(QThread):
    """Background thread for flashing partitions"""
    progress = pyqtSignal(str, int, int)
    status = pyqtSignal(str, int)
    completed = pyqtSignal(bool, str)
    
    def __init__(
        self,
        flasher: PartitionFlasher,
        emulator: AndroidEmulator,
        partitions: Dict[str, str],
        workspace_dir: Optional[Path],
    ):
        super().__init__()
        self.flasher = flasher
        self.emulator = emulator
        self.partitions = partitions
        self.workspace_dir = workspace_dir
        self._cancel_requested = False
    
    def run(self):
        success = self._flash_emulator()
        
        if success:
            self.completed.emit(True, "האמולטור הותחל בהצלחה עם המחיצות!")
        else:
            if self._cancel_requested:
                self.completed.emit(False, "צריבה בוטלה על ידי משתמש")
            else:
                details = self.emulator.last_error.strip() if getattr(self.emulator, "last_error", "") else ""
                msg = "צריבה לאמולטור נכשלה. בדוק SDK/AVD ולוגים."
                if details:
                    msg += f"\nסיבה: {details}"
                self.completed.emit(False, msg)
    
    def _flash_emulator(self) -> bool:
        """Flash partitions to Android Emulator"""
        if not self.workspace_dir:
            self.status.emit("workspace", -1)
            return False

        # Mark per-partition progress at start so user sees activity.
        for partition_name in self.partitions.keys():
            if self._cancel_requested:
                return False
            self.status.emit(partition_name, 1)

        return self.emulator.flash_partitions_to_emulator(
            self.partitions,
            self.workspace_dir,
            progress_callback=lambda name, curr, total: self.progress.emit(name, curr, total),
            status_callback=lambda name, pct: self.status.emit(name, pct),
            cancel_check=lambda: self._cancel_requested,
        )
    
    def request_cancel(self):
        """Request cancellation of flashing"""
        self._cancel_requested = True


class FlashingDialog(QDialog):
    """Dialog showing flashing progress"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("צריבת מחיצות")
        self.setGeometry(100, 100, 600, 500)
        self.setModal(True)
        self.flashing_thread = None
        
        layout = QVBoxLayout(self)
        
        # Title label
        title_label = QLabel("צריבת מחיצות למכשיר")
        title_font = title_label.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Status label
        self.status_label = QLabel("מתחיל צריבה...")
        self.status_label.setStyleSheet("padding: 10px; background: #f0f0f0; border-radius: 4px;")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ccc;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Current partition label
        self.current_partition_label = QLabel("מעובד: ...")
        layout.addWidget(self.current_partition_label)
        
        # Log area
        log_label = QLabel("פרטי צריבה:")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("בטל צריבה")
        self.cancel_btn.setStyleSheet("background-color: #ff6b6b; color: white; font-weight: bold;")
        self.cancel_btn.clicked.connect(self.cancel_flashing)
        button_layout.addWidget(self.cancel_btn)
        
        self.close_btn = QPushButton("סגור")
        self.close_btn.setEnabled(False)
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def set_flashing_thread(self, thread: 'FlashingThread'):
        """Set the flashing thread reference"""
        self.flashing_thread = thread
    
    def cancel_flashing(self):
        """Cancel the flashing process"""
        if self.flashing_thread:
            self.log_text.append("\n[!] ביטול צריבה... (יתבטל לאחר הפרטישן הנוכחי)")
            self.flashing_thread.request_cancel()
            self.cancel_btn.setEnabled(False)
    
    def update_status(self, partition_name: str, current: int, total: int):
        """Update flashing status"""
        self.status_label.setText(f"צריבת {partition_name}... ({current}/{total})")
        progress = int((current / total) * 100)
        self.progress_bar.setValue(progress)
        self.current_partition_label.setText(f"מעובד: {partition_name}")
        self.log_text.append(f"[צריבה] {partition_name} ({current}/{total})")
        self.log_text.ensureCursorVisible()
    
    def update_partition_status(self, partition_name: str, percentage: int):
        """Update individual partition status"""
        if percentage == 100:
            self.log_text.append(f"✓ {partition_name} - הצליחה")
        elif percentage == -1:
            self.log_text.append(f"✗ {partition_name} - נכשלה")
        else:
            self.log_text.append(f"• {partition_name} - {percentage}%")
        self.progress_bar.setValue(min(95, percentage))
        self.log_text.ensureCursorVisible()
    
    def on_completed(self, success: bool, message: str):
        """Called when flashing completes"""
        if success:
            self.log_text.append("\n" + "="*40)
            self.log_text.append("✓ צריבה הסתיימה בהצלחה!")
            self.log_text.append("="*40)
            self.status_label.setText("✓ צריבה הסתיימה בהצלחה!")
            self.status_label.setStyleSheet("padding: 10px; background: #c8e6c9; font-weight: bold; color: green; border-radius: 4px;")
            self.progress_bar.setValue(100)
        else:
            self.log_text.append("\n" + "="*40)
            self.log_text.append(f"✗ שגיאה: {message}")
            self.log_text.append("="*40)
            self.status_label.setText(f"✗ שגיאה: {message}")
            self.status_label.setStyleSheet("padding: 10px; background: #ffcdd2; font-weight: bold; color: red; border-radius: 4px;")
            # Keep failure bar visually honest (not 100% on failure).
            if self.progress_bar.value() > 95:
                self.progress_bar.setValue(95)

        self.cancel_btn.setEnabled(False)
        self.close_btn.setEnabled(True)
        self.log_text.ensureCursorVisible()



class PreviewPanel(QWidget):
    """Panel showing live preview of device modifications"""
    
    def __init__(self, config):
        super().__init__()
        
        self.config = config
        self.i18n = get_i18n()
        self.current_preview = None
        self.extracted_partitions: Dict[str, str] = {}
        self.partition_names: List[str] = []
        self.preview_metadata: Dict[str, object] = {}
        self.custom_logo_path: Optional[str] = None
        self.workspace_dir: Optional[Path] = None
        
        # Partition Flasher
        self.flasher = PartitionFlasher(config)
        self.emulator = AndroidEmulator(config)
        self.flashing_thread: Optional[FlashingThread] = None
        
        self.init_ui()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_preview)
    
    def init_ui(self):
        """Initialize UI elements"""
        layout = QVBoxLayout(self)
        
        # Preview group
        preview_group = QGroupBox(self.i18n.t('preview_panel.title'))
        preview_layout = QVBoxLayout()
        
        # Flash controls (top section)
        flash_controls = QHBoxLayout()
        
        self.flash_btn = QPushButton("🔥 צרוב מחיצות לאמולטור")
        self.flash_btn.clicked.connect(self.flash_partitions)
        self.flash_btn.setStyleSheet("font-weight: bold; padding: 8px; background-color: #ff6b6b; color: white;")
        self.flash_btn.setEnabled(False)
        flash_controls.addWidget(self.flash_btn)
        
        preview_layout.addLayout(flash_controls)
        
        # Flash status label
        self.flash_status_label = QLabel("סטטוס: מחכה למחיצות")
        self.flash_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.flash_status_label.setStyleSheet("padding: 5px; background: #f0f0f0; border-radius: 4px;")
        preview_layout.addWidget(self.flash_status_label)
        
        # Screen preview label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(400, 750)
        self.preview_label.setStyleSheet("border: 2px solid #555; background: #f5f5f5;")
        
        # Show initial placeholder
        self.show_placeholder()
        
        preview_layout.addWidget(self.preview_label)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        refresh_btn = QPushButton(self.i18n.t('preview_panel.refresh'))
        refresh_btn.clicked.connect(self.update_preview)
        controls_layout.addWidget(refresh_btn)
        
        self.auto_refresh_btn = QPushButton(self.i18n.t('preview_panel.auto_refresh_enable'))
        self.auto_refresh_btn.setCheckable(True)
        self.auto_refresh_btn.toggled.connect(self.toggle_auto_refresh)
        controls_layout.addWidget(self.auto_refresh_btn)
        
        preview_layout.addLayout(controls_layout)
        
        # Info label
        self.info_label = QLabel(self.i18n.t('preview_panel.preview_info'))
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.info_label)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
    
    def show_placeholder(self):
        """Show placeholder preview image"""
        width, height = 380, 720
        
        # Create placeholder image
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(240, 240, 240))
        
        # Draw text
        painter = QPainter(pixmap)
        painter.setPen(QColor(100, 100, 100))
        font = QFont("Arial", 16)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, self.i18n.t('preview_panel.not_available'))
        painter.end()
        
        self.preview_label.setPixmap(pixmap)
    
    def update_preview(self):
        """Update preview with current modifications"""
        # If user provided a custom boot logo, show it first.
        if self.custom_logo_path:
            self.load_logo_preview(self.custom_logo_path)
            return

        # If partitions were extracted, build preview from extracted firmware set.
        if self.extracted_partitions:
            self.show_firmware_composition_preview()
            return

        # Fallback when no firmware context exists yet.
        self.show_simulated_boot_screen()

    def set_firmware_context(self, extracted_partitions: Dict[str, str], partition_names: Optional[List[str]] = None):
        """Set extracted firmware context for composition-based preview rendering."""
        self.extracted_partitions = extracted_partitions or {}
        self.partition_names = partition_names or []
        
        # Update flash button state
        if self.extracted_partitions:
            self.flash_btn.setEnabled(True)
            self.flash_status_label.setText("סטטוס: מוכן לצריבה")
        else:
            self.flash_btn.setEnabled(False)
            self.flash_status_label.setText("סטטוס: מחכה למחיצות")

    def set_custom_logo(self, logo_path: str):
        """Set custom logo source used by preview renderer."""
        self.custom_logo_path = logo_path
    
    def set_workspace_dir(self, workspace_dir: str):
        """Set workspace directory for emulator"""
        self.workspace_dir = Path(workspace_dir) if workspace_dir else None

    def set_preview_metadata(self, metadata: Dict[str, object]):
        """Set metadata produced by static preview engine."""
        self.preview_metadata = metadata or {}
    
    def flash_partitions(self):
        """Flash partitions into a real Android emulator instance"""
        if not self.extracted_partitions:
            QMessageBox.warning(
                self,
                "אין מחיצות",
                "אנא חלץ או ייבא מחיצות תחילה לפני צריבה."
            )
            return
        
        if not self.workspace_dir:
            QMessageBox.warning(
                self,
                "אין סביבת עבודה",
                "בחר תיקיית פרויקט לפני צריבה לאמולטור."
            )
            return

        if not self.emulator.is_available():
            QMessageBox.critical(
                self,
                "Android SDK חסר",
                "לא נמצא Android Emulator במחשב.\n"
                "התקן Android Studio / SDK Emulator ונסה שוב."
            )
            return

        result = QMessageBox.warning(
            self,
            "⚠️ צריבה לאמולטור",
            "התוכנה תיצור/תעדכן AVD אמיתי ותאתחל אותו עם קבצי המחיצות.\n\n"
            "להמשיך?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result != QMessageBox.StandardButton.Yes:
            return
        
        # Show flashing dialog
        dialog = FlashingDialog(self)
        
        # Create and start flashing thread
        self.flashing_thread = FlashingThread(
            self.flasher,
            self.emulator,
            self.extracted_partitions,
            self.workspace_dir,
        )
        dialog.set_flashing_thread(self.flashing_thread)
        
        self.flashing_thread.progress.connect(dialog.update_status)
        self.flashing_thread.status.connect(dialog.update_partition_status)
        self.flashing_thread.completed.connect(dialog.on_completed)
        self.flashing_thread.completed.connect(lambda success, msg: self._on_flash_completed(success, msg))
        self.flashing_thread.start()
        
        # Show dialog
        self.flash_status_label.setText("🔄 צריבה בתהליך (אמולטור)...")
        self.flash_btn.setEnabled(False)
        dialog.exec()
    
    def _on_flash_completed(self, success: bool, message: str):
        """Called when flashing completes"""
        if success:
            self.flash_status_label.setText("✓ צריבה הושלמה בהצלחה!")
            self.flash_status_label.setStyleSheet("padding: 5px; background: #c8e6c9; color: green; font-weight: bold;")
        else:
            self.flash_status_label.setText(f"✗ שגיאה: {message}")
            self.flash_status_label.setStyleSheet("padding: 5px; background: #ffcdd2; color: red; font-weight: bold;")
        
        self.flash_btn.setEnabled(True)

    def show_firmware_composition_preview(self):
        """Render a realistic Android phone preview based on extracted partitions."""
        width, height = 380, 720

        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(240, 240, 240))

        required = [
            'boot', 'system', 'vendor', 'vbmeta', 'dtbo', 'product', 'odm', 'super'
        ]
        present = set(name.lower() for name in self.extracted_partitions.keys())

        # consider aliases / split partitions
        has_system = any(p.startswith('system') for p in present)
        has_vendor = any(p.startswith('vendor') for p in present)
        has_product = any(p.startswith('product') for p in present)
        has_odm = any(p.startswith('odm') for p in present)
        has_super = 'super' in present

        present_required = []
        missing_required = []
        for name in required:
            ok = (
                (name == 'system' and has_system) or
                (name == 'vendor' and has_vendor) or
                (name == 'product' and has_product) or
                (name == 'odm' and has_odm) or
                (name == 'super' and has_super) or
                (name in present)
            )
            (present_required if ok else missing_required).append(name)

        can_boot = 'boot' in present and (has_system or has_super)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw realistic phone mockup
        self._draw_android_phone_mockup(
            painter, width, height, can_boot, present_required, missing_required,
            present, has_system, has_vendor, has_product, has_odm, has_super
        )

        painter.end()

        self.preview_label.setPixmap(pixmap)
        base_info = self.i18n.t('preview_panel.preview_composed_info')
        if self.preview_metadata:
            icons = self.preview_metadata.get("icon_count", 0)
            fw = self.preview_metadata.get("framework_apk")
            launcher = self.preview_metadata.get("launcher_apk")
            details = (
                f" | Static Engine: icons={icons}"
                f" | framework={'yes' if fw else 'no'}"
                f" | launcher={'yes' if launcher else 'no'}"
            )
            self.info_label.setText(base_info + details)
        else:
            self.info_label.setText(base_info)
    
    def _draw_android_phone_mockup(self, painter, width, height, can_boot, present_required, missing_required,
                                     present, has_system, has_vendor, has_product, has_odm, has_super):
        """Draw a realistic Android phone interface mockup."""
        from datetime import datetime
        
        # Phone frame (device bezel)
        frame_margin = 30
        phone_x, phone_y = frame_margin, frame_margin
        phone_w, phone_h = width - (frame_margin * 2), height - (frame_margin * 2)
        
        # Outer phone body (dark gray bezel)
        painter.setPen(QColor(50, 50, 50))
        painter.setBrush(QColor(40, 40, 40))
        painter.drawRoundedRect(phone_x, phone_y, phone_w, phone_h, 20, 20)
        
        # Screen area (slightly inset)
        screen_margin = 8
        screen_x = phone_x + screen_margin
        screen_y = phone_y + screen_margin + 35  # Space for front camera/speaker
        screen_w = phone_w - (screen_margin * 2)
        screen_h = phone_h - (screen_margin * 2) - 70  # Space for camera at top and buttons at bottom
        
        # Screen background
        painter.setPen(Qt.PenStyle.NoPen)
        if can_boot:
            painter.setBrush(QColor(245, 250, 255))  # Light blue-white for bootable system
        else:
            painter.setBrush(QColor(255, 245, 235))  # Warm white for incomplete system
        painter.drawRoundedRect(screen_x, screen_y, screen_w, screen_h, 8, 8)
        
        # Draw front camera notch/hole
        camera_x = screen_x + screen_w // 2 - 8
        camera_y = phone_y + screen_margin + 5
        painter.setBrush(QColor(20, 20, 20))
        painter.drawEllipse(camera_x, camera_y, 16, 16)
        
        # === ANDROID STATUS BAR ===
        status_bar_h = 24
        painter.setPen(QColor(255, 255, 255))
        painter.setBrush(QColor(33, 33, 33))
        painter.drawRect(screen_x, screen_y, screen_w, status_bar_h)
        
        # Time on left
        current_time = datetime.now().strftime("%H:%M")
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.drawText(screen_x + 8, screen_y + 17, current_time)
        
        # Status icons on right (battery, signal, wifi)
        icon_x = screen_x + screen_w - 12
        painter.setFont(QFont("Arial", 8))
        
        # Battery icon
        painter.drawText(icon_x - 30, screen_y + 17, "100%")
        painter.setPen(QColor(150, 255, 150))
        painter.drawRect(icon_x - 18, screen_y + 8, 14, 9)
        painter.fillRect(icon_x - 17, screen_y + 9, 12, 7, QColor(150, 255, 150))
        painter.fillRect(icon_x - 4, screen_y + 11, 2, 3, QColor(150, 255, 150))
        
        # Signal icon
        painter.setPen(QColor(200, 200, 200))
        for i in range(4):
            h = 3 + i * 2
            painter.fillRect(icon_x - 55 + i * 4, screen_y + 18 - h, 2, h, QColor(200, 200, 200))
        
        # === HOME SCREEN CONTENT ===
        content_y = screen_y + status_bar_h + 10
        
        # Date/Time widget
        painter.setPen(QColor(80, 80, 80))
        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        time_str = datetime.now().strftime("%H:%M")
        painter.drawText(screen_x + 12, content_y + 25, time_str)
        
        painter.setFont(QFont("Arial", 8))
        date_str = datetime.now().strftime("%A, %B %d")
        painter.drawText(screen_x + 12, content_y + 40, date_str)
        
        content_y += 55
        
        # System status card
        card_x, card_y = screen_x + 10, content_y
        card_w, card_h = screen_w - 20, 60
        
        painter.setPen(QColor(220, 220, 220))
        if can_boot:
            painter.setBrush(QColor(232, 245, 233))  # Light green background
        else:
            painter.setBrush(QColor(255, 243, 224))  # Light orange background
        painter.drawRoundedRect(card_x, card_y, card_w, card_h, 8, 8)
        
        # Status icon and text
        icon_y = card_y + 30
        if can_boot:
            painter.setPen(QColor(46, 125, 50))
            painter.setFont(QFont("Arial", 18))
            painter.drawText(card_x + 10, icon_y, "✓")
            painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            painter.drawText(card_x + 35, icon_y - 8, "System Ready")
            painter.setFont(QFont("Arial", 8))
            painter.setPen(QColor(76, 175, 80))
            painter.drawText(card_x + 35, icon_y + 8, "All critical partitions present")
        else:
            painter.setPen(QColor(230, 81, 0))
            painter.setFont(QFont("Arial", 18))
            painter.drawText(card_x + 10, icon_y, "⚠")
            painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            painter.drawText(card_x + 35, icon_y - 8, "Incomplete System")
            painter.setFont(QFont("Arial", 8))
            painter.setPen(QColor(255, 152, 0))
            painter.drawText(card_x + 35, icon_y + 8, "Missing critical partitions")
        
        content_y += card_h + 20
        
        # App drawer label
        painter.setPen(QColor(100, 100, 100))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.drawText(screen_x + 12, content_y, "Applications")
        
        content_y += 18
        
        # App icons grid (simulated home screen)
        icon_size = 44
        icon_spacing = 58
        icons_per_row = 4
        icon_start_x = screen_x + (screen_w - icons_per_row * icon_spacing) // 2 + 5
        icon_start_y = content_y
        
        # Define app icons to show based on what partitions are present
        apps = []
        if has_system or has_super:
            apps.extend([
                ("📞", "Phone", QColor(33, 150, 243)),
                ("💬", "Messages", QColor(76, 175, 80)),
                ("🌐", "Browser", QColor(255, 152, 0)),
                ("📷", "Camera", QColor(156, 39, 176)),
            ])
        if has_vendor or has_super:
            apps.extend([
                ("⚙️", "Settings", QColor(96, 125, 139)),
                ("📧", "Email", QColor(244, 67, 54)),
            ])
        if has_product or has_system:
            apps.extend([
                ("🎵", "Music", QColor(233, 30, 99)),
                ("📁", "Files", QColor(255, 193, 7)),
            ])
        
        # Additional apps if super partition exists (means full system)
        if has_super:
            apps.extend([
                ("🎮", "Games", QColor(121, 85, 72)),
                ("📊", "Clock", QColor(63, 81, 181)),
                ("🗺️", "Maps", QColor(0, 150, 136)),
                ("📝", "Notes", QColor(255, 87, 34)),
            ])
        
        # Draw app icons
        row, col = 0, 0
        
        for emoji, label, color in apps:
            if row >= 3:  # Limit to 3 rows
                break
                
            x = icon_start_x + col * icon_spacing
            y = icon_start_y + row * (icon_spacing + 15)
            
            # Icon background (circular)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(x, y, icon_size, icon_size)
            
            # Icon emoji
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Segoe UI Emoji", 22))
            painter.drawText(x + 10, y + 30, emoji)
            
            # App label
            painter.setPen(QColor(70, 70, 70))
            painter.setFont(QFont("Arial", 7))
            # Center the text
            label_width = len(label) * 4
            painter.drawText(x + (icon_size - label_width) // 2, y + icon_size + 12, label)
            
            col += 1
            if col >= icons_per_row:
                col = 0
                row += 1
        
        # === SYSTEM INFO FOOTER (Compact) ===
        footer_y = screen_y + screen_h - 80
        
        # Draw a subtle divider line
        painter.setPen(QColor(200, 200, 200))
        painter.drawLine(screen_x + 15, footer_y, screen_x + screen_w - 15, footer_y)
        
        footer_y += 12
        
        # System information in compact format
        painter.setPen(QColor(100, 100, 100))
        painter.setFont(QFont("Arial", 7))
        painter.drawText(screen_x + 12, footer_y, "FIRMWARE STATUS")
        
        footer_y += 14
        
        # Partition status chips (like Android material design)
        chip_x = screen_x + 12
        chip_y = footer_y - 10
        chip_spacing = 5
        
        critical = [
            ('boot', 'Boot'),
            ('system', 'System'), 
            ('vendor', 'Vendor'),
            ('super', 'Super')
        ]
        
        painter.setFont(QFont("Arial", 7, QFont.Weight.Bold))
        
        for part_name, display_name in critical:
            # Check if partition is present
            is_present = False
            if part_name == 'system':
                is_present = has_system
            elif part_name == 'vendor':
                is_present = has_vendor
            elif part_name == 'super':
                is_present = has_super
            else:
                is_present = part_name in [p.lower() for p in present_required]
            
            # Calculate chip width based on text
            chip_width = len(display_name) * 5 + 14
            chip_height = 16
            
            # Draw chip background
            painter.setPen(Qt.PenStyle.NoPen)
            if is_present:
                painter.setBrush(QColor(200, 230, 201))  # Light green
            else:
                painter.setBrush(QColor(255, 205, 210))  # Light red
            painter.drawRoundedRect(chip_x, chip_y, chip_width, chip_height, 8, 8)
            
            # Draw status indicator dot
            dot_x = chip_x + 5
            dot_y = chip_y + 8
            if is_present:
                painter.setBrush(QColor(76, 175, 80))  # Green dot
            else:
                painter.setBrush(QColor(244, 67, 54))  # Red dot
            painter.drawEllipse(dot_x - 2, dot_y - 2, 4, 4)
            
            # Draw text
            if is_present:
                painter.setPen(QColor(46, 125, 50))  # Dark green text
            else:
                painter.setPen(QColor(198, 40, 40))  # Dark red text
            painter.drawText(chip_x + 12, chip_y + 11, display_name)
            
            # Move to next chip position
            chip_x += chip_width + chip_spacing
            
            # Wrap to next line if needed
            if chip_x > screen_x + screen_w - chip_width:
                chip_x = screen_x + 12
                chip_y += chip_height + 4
        
        # === NAVIGATION BAR ===
        nav_bar_h = 40
        nav_bar_y = screen_y + screen_h - nav_bar_h
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(250, 250, 250))
        painter.drawRect(screen_x, nav_bar_y, screen_w, nav_bar_h)
        
        # Navigation buttons (Back, Home, Recent Apps)
        nav_center = screen_x + screen_w // 2
        button_y = nav_bar_y + nav_bar_h // 2
        
        painter.setPen(QColor(100, 100, 100))
        painter.setBrush(QColor(100, 100, 100))
        
        # Back button (triangle)
        back_x = nav_center - 70
        triangle = QPolygon([
            QPoint(back_x + 8, button_y),
            QPoint(back_x, button_y - 6),
            QPoint(back_x, button_y + 6)
        ])
        painter.drawPolygon(triangle)
        
        # Home button (circle)
        home_x = nav_center
        painter.drawEllipse(home_x - 8, button_y - 8, 16, 16)
        
        # Recent apps (square)
        recent_x = nav_center + 70
        painter.drawRect(recent_x - 8, button_y - 8, 16, 16)
    
    def show_simulated_boot_screen(self):
        """Show simulated Android boot screen"""
        width, height = 380, 720
        
        # Create boot screen image
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(0, 0, 0))
        
        # Draw simulated logo
        painter = QPainter(pixmap)
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Arial", 24, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(
            pixmap.rect(), 
            Qt.AlignmentFlag.AlignCenter, 
            "ANDROID"
        )
        
        # Draw version info
        font_small = QFont("Arial", 10)
        painter.setFont(font_small)
        painter.drawText(
            20, height - 40,
            "Custom ROM - Modified"
        )
        
        painter.end()
        
        self.preview_label.setPixmap(pixmap)
        self.info_label.setText(self.i18n.t('preview_panel.preview_info') + " (Simulated)")
    
    def toggle_auto_refresh(self, enabled):
        """Toggle auto-refresh of preview"""
        if enabled:
            self.refresh_timer.start(1000)  # Refresh every second
            self.auto_refresh_btn.setText(self.i18n.t('preview_panel.auto_refresh_disable'))
        else:
            self.refresh_timer.stop()
            self.auto_refresh_btn.setText(self.i18n.t('preview_panel.auto_refresh_enable'))
    
    def load_logo_preview(self, logo_path: str):
        """Load and display boot logo preview"""
        try:
            # Load image
            img = Image.open(logo_path)
            
            # Resize to fit preview
            img.thumbnail((380, 720), Image.Resampling.LANCZOS)
            
            # Convert to QPixmap
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            pixmap = QPixmap()
            pixmap.loadFromData(img_bytes.getvalue())
            
            self.preview_label.setPixmap(pixmap)
            self.info_label.setText(self.i18n.t('preview_panel.preview_logo_info'))
            
        except Exception as e:
            self.show_placeholder()
            self.info_label.setText(f"Error loading preview: {e}")
