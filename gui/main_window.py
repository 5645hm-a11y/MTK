"""
Main Window GUI
Primary interface for MTK Firmware Editor
"""

import logging
import math
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QTabWidget,
    QTableWidget, QTableWidgetItem, QProgressBar,
    QFileDialog, QMessageBox, QSplitter, QGroupBox,
    QListWidget, QStatusBar, QToolBar, QMenuBar, QMenu
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QIcon

from core.device_interface import DeviceInterface, DeviceMode
from core.partition_extractor import PartitionExtractor
from core.scatter_generator import ScatterFileGenerator
from core.firmware_editor import FirmwareEditor
from core.enhanced_detector import EnhancedDeviceDetector
from core.workflow_engine import WorkflowEngine
from gui.device_panel import DevicePanel
from gui.partition_panel import PartitionPanel
from gui.editor_panel import EditorPanel
from gui.preview_panel import PreviewPanel
from utils.i18n import get_i18n


class ExtractionThread(QThread):
    """Background extraction worker to keep UI responsive on large partitions."""

    partitions_ready = pyqtSignal(object)
    progress = pyqtSignal(str, int, int)
    partition_status = pyqtSignal(str, str, str)
    completed = pyqtSignal(dict, dict, list)
    failed = pyqtSignal(str)

    def __init__(self, extractor: PartitionExtractor, output_dir: Path):
        super().__init__()
        self.extractor = extractor
        self.output_dir = output_dir

    def run(self):
        try:
            partitions = self.extractor.partitions if self.extractor.partitions else self.extractor.read_partition_table()
            self.partitions_ready.emit(partitions)

            extracted = self.extractor.extract_all_partitions(
                self.output_dir,
                lambda name, current, total: self.progress.emit(name, current, total),
                lambda name, status, err: self.partition_status.emit(name, status, err)
            )
            self.completed.emit(
                extracted,
                self.extractor.last_failed_partitions.copy(),
                [p.name for p in self.extractor.partitions]
            )
        except Exception as e:
            self.failed.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, config):
        super().__init__()
        
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.i18n = get_i18n()
        
        # Core components
        self.device = DeviceInterface(config)
        self.enhanced_detector = EnhancedDeviceDetector(config)
        self.extractor = None
        self.scatter_gen = ScatterFileGenerator(config)
        self.editor = FirmwareEditor(config)
        self.workflow = WorkflowEngine(config)
        
        # State
        self.workspace_dir = None
        self.extracted_partitions = {}
        self.extraction_thread = None
        
        # Setup UI
        self.init_ui()
        
        # Device detection timer - only start when needed
        # (Don't auto-scan continuously, let user control it)
        # self.device_timer = QTimer()
        # self.device_timer.timeout.connect(self.check_device_connection)
        # self.device_timer.start(2000)  # Check every 2 seconds
    
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle(self.i18n.t('app.name'))
        self.setGeometry(100, 100, 1600, 900)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Device and Partitions
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.device_panel = DevicePanel(self.device, self.config)
        self.partition_panel = PartitionPanel(self.config)
        
        left_layout.addWidget(self.device_panel, 1)
        left_layout.addWidget(self.partition_panel, 2)
        
        # Right panel - Tabs
        self.tab_widget = QTabWidget()
        
        # Editor tab
        self.editor_panel = EditorPanel(self.editor, self.config)
        self.tab_widget.addTab(self.editor_panel, self.i18n.t('editor_panel.title'))
        
        # Preview tab
        self.preview_panel = PreviewPanel(self.config)
        self.tab_widget.addTab(self.preview_panel, self.i18n.t('preview_panel.title'))
        
        # Log tab
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.tab_widget.addTab(self.log_widget, "Log")
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(self.tab_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(self.i18n.t('status.ready'))
        
        # Connect signals
        self.connect_signals()
    
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu(self.i18n.t('menu.file'))
        
        open_workspace_action = QAction(self.i18n.t('menu.file_open_workspace'), self)
        open_workspace_action.triggered.connect(self.open_workspace)
        file_menu.addAction(open_workspace_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(self.i18n.t('menu.file_exit'), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Device menu
        device_menu = menubar.addMenu(self.i18n.t('menu.device'))
        
        detect_action = QAction(self.i18n.t('menu.device_detect'), self)
        detect_action.triggered.connect(self.detect_device)
        device_menu.addAction(detect_action)
        
        extract_action = QAction(self.i18n.t('menu.device_extract_all'), self)
        extract_action.triggered.connect(self.extract_all_partitions)
        device_menu.addAction(extract_action)
        
        # Tools menu
        tools_menu = menubar.addMenu(self.i18n.t('menu.tools'))
        
        generate_scatter_action = QAction(self.i18n.t('menu.tools_generate_scatter'), self)
        generate_scatter_action.triggered.connect(self.generate_scatter)
        tools_menu.addAction(generate_scatter_action)
        
        export_action = QAction(self.i18n.t('menu.tools_export_firmware'), self)
        export_action.triggered.connect(self.export_firmware)
        tools_menu.addAction(export_action)
        
        # Language menu
        language_menu = menubar.addMenu("Language / שפה / Langue")
        
        hebrew_action = QAction("עברית (Hebrew)", self)
        hebrew_action.triggered.connect(lambda: self.change_language('he'))
        language_menu.addAction(hebrew_action)
        
        english_action = QAction("English", self)
        english_action.triggered.connect(lambda: self.change_language('en'))
        language_menu.addAction(english_action)
        
        french_action = QAction("Français (French)", self)
        french_action.triggered.connect(lambda: self.change_language('fr'))
        language_menu.addAction(french_action)
        
        # Help menu
        help_menu = menubar.addMenu(self.i18n.t('menu.help'))
        
        about_action = QAction(self.i18n.t('menu.help_about'), self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def change_language(self, language_code: str):
        """Change application language"""
        # Get the new language name before changing
        temp_current_lang = self.i18n.current_language
        self.i18n.set_language(language_code)
        new_lang_name = self.i18n.get_language_name()
        
        # Revert to show message in current language
        self.i18n.set_language(temp_current_lang)
        
        # Show restart message in CURRENT language
        QMessageBox.information(
            self,
            self.i18n.t('messages.language_changed'),
            self.i18n.t('messages.restart_required', language=new_lang_name)
        )
        
        # Now actually change the language
        self.i18n.set_language(language_code)
        self.config.set('application.language', language_code)
        self.config.save_config()
    
    def create_toolbar(self):
        """Create application toolbar"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Device detection button
        detect_btn = QPushButton(self.i18n.t('toolbar.detect_device'))
        detect_btn.clicked.connect(self.detect_device)
        toolbar.addWidget(detect_btn)
        
        toolbar.addSeparator()
        
        # Extract button
        extract_btn = QPushButton(self.i18n.t('toolbar.extract_partitions'))
        extract_btn.clicked.connect(self.extract_all_partitions)
        toolbar.addWidget(extract_btn)
        
        # Import button
        import_btn = QPushButton(self.i18n.t('toolbar.import_partitions'))
        import_btn.clicked.connect(self.import_existing_partitions)
        toolbar.addWidget(import_btn)
        
        toolbar.addSeparator()
        
        # Generate scatter button
        scatter_btn = QPushButton(self.i18n.t('toolbar.generate_scatter'))
        scatter_btn.clicked.connect(self.generate_scatter)
        toolbar.addWidget(scatter_btn)
        
        toolbar.addSeparator()
        
        # Export button
        export_btn = QPushButton(self.i18n.t('toolbar.export_firmware'))
        export_btn.clicked.connect(self.export_firmware)
        toolbar.addWidget(export_btn)
    
    def connect_signals(self):
        """Connect UI signals"""
        self.device_panel.device_detected.connect(self.on_device_detected)
        self.partition_panel.partition_selected.connect(self.on_partition_selected)
        self.editor_panel.modification_made.connect(self.on_modification_made)
    
    def check_device_connection(self):
        """Periodically check for device connection"""
        try:
            if not self.device_panel.is_connected():
                self.device.detect_device()
                if self.device.mode != DeviceMode.UNKNOWN:
                    self.device_panel.update_device_info(self.device.get_device_info())
                    if self.extractor is None:
                        self.extractor = PartitionExtractor(self.device, self.config)
        except Exception as e:
            self.logger.debug(f"Device check failed: {e}")
    
    def detect_device(self):
        """Manually trigger device detection"""
        self.status_bar.showMessage(self.i18n.t('messages.detecting_device'))
        
        # Try enhanced detection first
        detected_devices = self.enhanced_detector.detect_all_modes()
        
        if detected_devices:
            self.logger.info(f"Enhanced detector found {len(detected_devices)} device(s)")
            
            # Get best device
            best_device = self.enhanced_detector.get_best_device()
            
            raw_state = best_device.get('state', 'Unknown')
            mode_label = raw_state.value if hasattr(raw_state, 'value') else str(raw_state)

            # Create device info
            device_info = {
                'mode': mode_label,
                'connected': True,
                'detection_method': best_device.get('method', 'Unknown'),
                'friendly_name': best_device.get('friendly_name', 'MTK Device')
            }
            
            if 'vid' in best_device:
                device_info['vid'] = best_device['vid']
            if 'pid' in best_device:
                device_info['pid'] = best_device['pid']
            
            self.device_panel.update_device_info(device_info)
            self.status_bar.showMessage(
                self.i18n.t('messages.device_detected', mode=device_info['mode'])
            )
            
            # Initialize extractor
            self.extractor = PartitionExtractor(self.device, self.config)
            
            QMessageBox.information(
                self,
                self.i18n.t('messages.success'),
                self.i18n.t('messages.device_found', 
                           mode=device_info['mode'],
                           name=device_info['friendly_name'])
            )
            return
        
        # Fallback to standard detection
        if self.device.detect_device():
            info = self.device.get_device_info()
            self.device_panel.update_device_info(info)
            self.status_bar.showMessage(
                self.i18n.t('messages.device_detected', mode=info.get('mode', 'Unknown'))
            )
            
            # Initialize extractor
            self.extractor = PartitionExtractor(self.device, self.config)
            
            QMessageBox.information(
                self,
                self.i18n.t('messages.success'),
                self.i18n.t('messages.device_detected', mode=info.get('mode', 'Unknown'))
            )
        else:
            self.status_bar.showMessage(self.i18n.t('messages.no_device'))
            
            # Check if device in brick/error state
            if self.enhanced_detector.check_for_brick_recovery():
                QMessageBox.warning(
                    self,
                    self.i18n.t('messages.brick_detected_title'),
                    self.i18n.t('messages.brick_detected_message')
                )
            else:
                QMessageBox.warning(
                    self,
                    self.i18n.t('messages.no_device_title'),
                    self.i18n.t('messages.no_device_message')
                )
    
    def extract_all_partitions(self):
        """Extract all partitions from device"""
        if not self.extractor:
            QMessageBox.warning(
                self, 
                self.i18n.t('messages.error'), 
                self.i18n.t('messages.detect_first')
            )
            return
        
        # Ask user where to save extracted partitions
        default_dir = str(Path(self.workspace_dir) / "extracted_partitions") if self.workspace_dir else ""
        output_dir_str = QFileDialog.getExistingDirectory(
            self,
            "בחר תיקייה לשמירת המחיצות",
            default_dir,
            QFileDialog.ShowDirsOnly
        )
        
        if not output_dir_str:
            return
        
        output_dir = Path(output_dir_str)

        # Preflight: estimate required size and validate free disk space.
        partitions = self.extractor.read_partition_table()
        self.partition_panel.load_partitions(partitions)

        required_bytes = self.extractor.estimate_required_extraction_size(partitions)
        has_space, free_bytes = self.extractor.has_enough_output_space(output_dir, required_bytes)
        if not has_space:
            required_gb = required_bytes / (1024 ** 3)
            free_gb = free_bytes / (1024 ** 3)
            QMessageBox.warning(
                self,
                self.i18n.t('messages.warning'),
                f"אין מספיק מקום פנוי לדגימת כל המחיצות הנדרשות.\n\n"
                f"נדרש בערך: {required_gb:.2f} GB\n"
                f"זמין כרגע: {free_gb:.2f} GB\n\n"
                f"אנא בחר תיקיית עבודה בכונן עם יותר מקום פנוי."
            )
            self.log_widget.append(
                f"[WARN] Not enough disk space. required~{required_gb:.2f}GB free={free_gb:.2f}GB"
            )
            return
        
        self.status_bar.showMessage(self.i18n.t('messages.extracting_partitions'))

        # Prevent parallel extraction jobs
        if self.extraction_thread and self.extraction_thread.isRunning():
            return

        self.extraction_thread = ExtractionThread(self.extractor, output_dir)
        self.extraction_thread.partitions_ready.connect(self.partition_panel.load_partitions)
        self.extraction_thread.progress.connect(self.partition_panel.update_extraction_progress)
        self.extraction_thread.partition_status.connect(self.partition_panel.update_partition_status)
        self.extraction_thread.completed.connect(self.on_extraction_completed)
        self.extraction_thread.failed.connect(self.on_extraction_failed)
        self.extraction_thread.start()

    def on_extraction_completed(self, extracted: dict, failed_partitions: dict, partition_names: list):
        """Handle extraction completion from background thread"""
        self.extracted_partitions = extracted

        # Build preview from extracted partition set
        self.preview_panel.set_firmware_context(self.extracted_partitions, partition_names)
        self.preview_panel.set_workspace_dir(self.workspace_dir)
        self.preview_panel.update_preview()

        required_names = [
            p.name for p in self.extractor.partitions
            if self.extractor._is_required_for_build(p)
        ]
        missing_required = [name for name in required_names if name not in extracted]
        has_super = any(name.lower() == 'super' for name in extracted.keys())

        if missing_required or failed_partitions:
            self.status_bar.showMessage("Extraction completed with errors")
            details = (
                f"Extracted: {len(extracted)} / Required: {len(required_names)}\n"
                f"Failed/Missing: {len(set(missing_required + list(failed_partitions.keys())))}\n"
                f"SUPER: {'OK' if has_super else 'MISSING'}"
            )
            QMessageBox.warning(
                self,
                self.i18n.t('messages.warning'),
                "Partition extraction finished with errors.\n\n" + details
            )
        else:
            self.status_bar.showMessage(self.i18n.t('messages.extraction_complete_status'))
            QMessageBox.information(
                self,
                self.i18n.t('messages.success'),
                self.i18n.t('messages.extraction_complete', count=len(self.extracted_partitions)) + "\n\nSUPER: OK"
            )

    def on_extraction_failed(self, error_text: str):
        """Handle extraction failure from background thread"""
        self.logger.error(f"Extraction failed: {error_text}")
        if "No space left on device" in error_text:
            QMessageBox.critical(
                self,
                self.i18n.t('messages.error'),
                "החילוץ נכשל כי נגמר המקום בכונן היעד.\n"
                "בחר תיקיית עבודה בכונן עם יותר מקום פנוי ונסה שוב."
            )
            return
        QMessageBox.critical(self, self.i18n.t('messages.error'), f"Extraction failed: {error_text}")
    
    def import_existing_partitions(self):
        """Import partition files from an existing directory"""
        from core.partition_extractor import PartitionInfo
        try:
            # Select directory containing partition files
            partition_dir = QFileDialog.getExistingDirectory(
                self,
                self.i18n.t('messages.select_partition_folder')
            )

            if not partition_dir:
                return

            partition_path = Path(partition_dir)

            # Find all .img files in the directory
            img_files = list(partition_path.glob("*.img"))

            if not img_files:
                QMessageBox.warning(
                    self,
                    self.i18n.t('messages.warning'),
                    self.i18n.t('messages.no_partition_files')
                )
                return

            # Build partition objects and dictionary from files
            imported_partitions = {}
            partition_names = []
            partition_objects = []

            # Sort files by name for consistent ordering
            img_files.sort(key=lambda f: f.name)

            for idx, img_file in enumerate(img_files):
                partition_name = img_file.stem  # Remove .img extension
                file_size = img_file.stat().st_size

                # Create PartitionInfo object
                partition_info = PartitionInfo(
                    name=partition_name,
                    size=file_size,
                    offset=idx * 0x1000000,  # Dummy offset
                    type="EMMC",
                    file_path=str(img_file),
                    is_image=True
                )

                partition_objects.append(partition_info)
                imported_partitions[partition_name] = str(img_file)
                partition_names.append(partition_name)

                self.logger.info(f"Imported partition: {partition_name} ({file_size / (1024**2):.2f} MB)")

            # Update application state
            scatter_candidates = sorted(partition_path.glob("*scatter*.txt"))
            scatter_path = scatter_candidates[0] if scatter_candidates else None

            validation_report = self.workflow.validate_input(imported_partitions, scatter_path)
            try:
                prepared_partitions = self.workflow.prepare_images(imported_partitions, partition_path)
            except Exception as e:
                self.logger.warning(f"prepare_images failed, fallback to original files: {e}")
                prepared_partitions = imported_partitions

            try:
                preview_meta = self.workflow.build_preview_metadata(partition_path)
            except Exception as e:
                self.logger.warning(f"build_preview_metadata failed: {e}")
                preview_meta = {}

            self.extracted_partitions = prepared_partitions
            self.workspace_dir = str(partition_path)

            # Initialize extractor if not already initialized
            if not self.extractor:
                self.extractor = PartitionExtractor(self.device, self.config)

            # Set the imported partitions in the extractor
            self.extractor.partitions = partition_objects

            # Load partitions into the partition panel table
            self.partition_panel.load_partitions(partition_objects)

            # Mark all as successfully imported (green)
            for partition_name in partition_names:
                self.partition_panel.update_partition_status(
                    partition_name,
                    'success',
                    ''
                )

            # Update preview panel with imported partitions
            self.preview_panel.set_firmware_context(self.extracted_partitions, partition_names)
            self.preview_panel.set_workspace_dir(self.workspace_dir)
            self.preview_panel.set_preview_metadata(preview_meta)
            self.preview_panel.update_preview()

            # Show success message
            self.status_bar.showMessage(
                self.i18n.t('messages.partitions_imported', count=len(imported_partitions))
            )
            QMessageBox.information(
                self,
                self.i18n.t('messages.success'),
                self.i18n.t('messages.partitions_imported', count=len(imported_partitions)) +
                f"\n\nמחיצות שיובאו:\n" + "\n".join(f"• {name}" for name in sorted(partition_names)) +
                f"\n\nגרסת אנדרואיד (משוערת): {validation_report.get('android_version', 'Unknown')}" +
                f"\nמחיצות Sparse: {len(validation_report.get('sparse_partitions', []))}" +
                f"\nScatter: {'נמצא' if validation_report.get('scatter_exists') else 'לא נמצא'}" +
                f"\nפערי Scatter: {len(validation_report.get('scatter_details', {}).get('missing_in_scatter', []))}"
            )

            self.logger.info(f"Successfully imported {len(imported_partitions)} partition files from {partition_dir}")
        except Exception as e:
            self.logger.exception("Import existing partitions crashed")
            QMessageBox.critical(
                self,
                self.i18n.t('messages.error'),
                f"Import failed safely (no crash): {e}"
            )
    
    def generate_scatter(self):
        """Generate scatter file for SP Flash Tool"""
        if not self.extractor or not self.extractor.partitions:
            QMessageBox.warning(
                self, 
                self.i18n.t('messages.error'), 
                self.i18n.t('messages.no_partitions')
            )
            return
        
        # Get output file
        scatter_file, _ = QFileDialog.getSaveFileName(
            self,
            self.i18n.t('workspace.save_scatter'),
            "MT_Android_scatter.txt",
            "Scatter Files (*.txt)"
        )
        
        if not scatter_file:
            return
        
        try:
            self.scatter_gen.generate(
                self.extractor.partitions,
                Path(scatter_file)
            )
            
            self.status_bar.showMessage(
                self.i18n.t('messages.scatter_created', path=scatter_file)
            )
            QMessageBox.information(
                self,
                self.i18n.t('messages.success'),
                self.i18n.t('messages.scatter_created', path=scatter_file)
            )
            
        except Exception as e:
            self.logger.error(f"Scatter generation failed: {e}")
            QMessageBox.critical(
                self, 
                self.i18n.t('messages.error'), 
                f"Failed to generate scatter file: {e}"
            )
    
    def export_firmware(self):
        """Export modified firmware as flashable package"""
        if not self.editor.partitions:
            QMessageBox.warning(
                self, 
                self.i18n.t('messages.error'), 
                self.i18n.t('messages.no_modifications')
            )
            return
        
        # Get output directory
        output_dir = QFileDialog.getExistingDirectory(
            self, self.i18n.t('messages.select_workspace')
        )
        
        if not output_dir:
            return
        
        try:
            output_path = Path(output_dir)
            
            # Export modified partitions
            exported = self.editor.export_modified_firmware(output_path)
            
            # Generate scatter file
            if self.extractor and self.extractor.partitions:
                scatter_path = output_path / "MT_Android_scatter.txt"
                self.scatter_gen.generate(
                    self.extractor.partitions,
                    scatter_path
                )
            
            # Create ZIP package
            # TODO: Implement ZIP creation with all files
            
            self.status_bar.showMessage(
                self.i18n.t('messages.firmware_exported', path=output_dir)
            )
            QMessageBox.information(
                self,
                self.i18n.t('messages.success'),
                self.i18n.t('messages.firmware_exported', path=output_dir)
            )
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            QMessageBox.critical(
                self, 
                self.i18n.t('messages.error'), 
                f"Export failed: {e}"
            )
    
    def open_workspace(self):
        """Open existing workspace"""
        directory = QFileDialog.getExistingDirectory(
            self, self.i18n.t('workspace.select_workspace')
        )
        
        if directory:
            self.workspace_dir = directory
            self.status_bar.showMessage(f"{self.i18n.t('workspace.select_workspace')}: {directory}")
    
    def on_device_detected(self, info):
        """Handle device detection signal"""
        self.log_widget.append(f"Device detected: {info}")
        if self.extractor is None:
            self.extractor = PartitionExtractor(self.device, self.config)
    
    def on_partition_selected(self, partition_name):
        """Handle partition selection"""
        self.log_widget.append(f"Selected partition: {partition_name}")
        # Load partition into editor if available
        if partition_name in self.extracted_partitions:
            path = Path(self.extracted_partitions[partition_name])
            self.editor.load_partition(partition_name, path)
    
    def on_modification_made(self, details):
        """Handle modification event"""
        self.log_widget.append(f"Modification: {details}")
        if details.get('type') == 'boot_logo' and details.get('file'):
            self.preview_panel.set_custom_logo(details['file'])
        self.preview_panel.update_preview()
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            self.i18n.t('about.title'),
            self.i18n.t(
                'about.description',
                name=self.config.get('application.name'),
                version=self.config.get('application.version')
            )
        )
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.device.disconnect()
        event.accept()
