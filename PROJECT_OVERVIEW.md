# PROJECT OVERVIEW - MTK Firmware Editor Pro

## סקירת הפרויקט

### מטרה
תוכנה מקצועית מלאה לעריכת קושחות Android עבור מכשירי MediaTek, כולל:
- חיבור למכשירים (גם כשאינם נדלקים)
- חילוץ מחיצות
- עריכת קושחה
- תצוגה מקדימה חיה
- יצירת קבצי Scatter
- בדיקות ואימות
- ייצוא חבילות לצריבה

---

## ארכיטקטורה

### שכבות המערכת

```
┌─────────────────────────────────────────┐
│         GUI Layer (PyQt6)               │
│  - Main Window                          │
│  - Device/Partition/Editor/Preview      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Core Logic Layer                │
│  - Device Interface                     │
│  - Partition Extractor                  │
│  - Firmware Editor                      │
│  - Scatter Generator                    │
│  - Testing Framework                    │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      Hardware Communication Layer       │
│  - USB (PyUSB)                          │
│  - ADB (adb-shell)                      │
│  - MTK Protocol                         │
└─────────────────────────────────────────┘
```

---

## מבנה קבצים מפורט

```
MTK_Firmware_Editor/
│
├── main.py                    # נקודת כניסה ראשית
├── config.yaml               # קונפיגורציה
├── requirements.txt          # תלויות Python
│
├── README.md                 # תיעוד כללי
├── USER_GUIDE.md            # מדריך משתמש מפורט
├── PROJECT_OVERVIEW.md      # המסמך הזה
│
├── install.bat              # סקריפט התקנה Windows
├── run.bat                  # סקריפט הפעלה Windows
├── .gitignore              # Git ignore rules
│
├── core/                    # מודולים מרכזיים
│   ├── __init__.py
│   ├── device_interface.py      # תקשורת עם מכשיר
│   ├── partition_extractor.py   # חילוץ מחיצות
│   ├── scatter_generator.py     # יצירת scatter files
│   ├── firmware_editor.py       # עריכת קושחה
│   ├── firmware_test.py         # בדיקות ואימות
│   └── config_manager.py        # ניהול הגדרות
│
├── gui/                     # ממשק משתמש גרפי
│   ├── __init__.py
│   ├── main_window.py          # חלון ראשי
│   ├── device_panel.py         # פאנל מכשיר
│   ├── partition_panel.py      # פאנל מחיצות
│   ├── editor_panel.py         # פאנל עריכה
│   └── preview_panel.py        # פאנל תצוגה מקדימה
│
├── utils/                   # כלי עזר
│   ├── __init__.py
│   ├── logger.py               # מערכת logging
│   └── package_exporter.py     # ייצוא חבילות
│
└── logs/                    # קבצי log (נוצר אוטומטית)
```

---

## מודולים עיקריים

### 1. Device Interface (core/device_interface.py)

**תפקיד**: תקשורת עם מכשירי Android/MTK

**יכולות**:
- זיהוי מכשיר אוטומטי
- תמיכה במצבים: ADB, Fastboot, MTK Preloader, MTK Download
- שליחת פקודות MTK
- קבלת מידע על מכשיר

**מחלקות עיקריות**:
```python
class DeviceMode(Enum):
    UNKNOWN, ADB, FASTBOOT, MTK_PRELOADER, MTK_DOWNLOAD, OFFLINE

class DeviceInterface:
    detect_device() -> bool
    get_device_info() -> Dict
    send_mtk_command(command: bytes) -> bytes
    reboot_to_mode(target_mode) -> bool
```

---

### 2. Partition Extractor (core/partition_extractor.py)

**תפקיד**: חילוץ מחיצות קושחה מהמכשיר

**יכולות**:
- קריאת טבלת מחיצות (GPT/PMT)
- חילוץ מחיצות בודדות
- חילוץ כל המחיצות
- בדיקת checksums

**מחלקות עיקריות**:
```python
@dataclass
class PartitionInfo:
    name, size, offset, type, file_path, ...

class PartitionExtractor:
    read_partition_table() -> List[PartitionInfo]
    extract_partition(partition, output_dir) -> str
    extract_all_partitions(output_dir) -> Dict[str, str]
```

---

### 3. Scatter Generator (core/scatter_generator.py)

**תפקיד**: יצירת קבצי scatter עבור SP Flash Tool

**יכולות**:
- יצירת scatter from partitions
- פרסור scatter קיים
- עדכון scatter עם שינויים

**מחלקות עיקריות**:
```python
class ScatterFileGenerator:
    generate(partitions, output_path, chip_model) -> str
    parse_scatter_file(scatter_path) -> List[PartitionInfo]
    update_scatter_file(scatter_path, updated_partitions) -> str
```

**פורמט Scatter**:
```
- general: MTK_PLATFORM_CFG
  platform: MT6580
  storage: EMMC
  
- partition_index: SYS0
  partition_name: preloader
  file_name: preloader.img
  linear_start_addr: 0x00000000
  ...
```

---

### 4. Firmware Editor (core/firmware_editor.py)

**תפקיד**: עריכה ושינוי של מחיצות קושחה

**יכולות**:
- שינוי Boot Logo
- עריכת build.prop
- הזרקת קבצים למחיצות
- ניהול workspace
- יומן שינויים

**מחלקות עיקריות**:
```python
class FirmwareEditor:
    create_workspace(base_dir) -> Path
    load_partition(partition_name, file_path) -> bool
    modify_boot_logo(logo_image_path) -> bool
    modify_build_prop(properties: Dict) -> bool
    inject_file(partition, source, target) -> bool
    export_modified_firmware(output_dir) -> Dict
```

---

### 5. Firmware Test (core/firmware_test.py)

**תפקיד**: בדיקות ואימות של קושחה מוערכת

**יכולות**:
- בדיקת גדלי מחיצות
- בדיקת תקינות קבצים
- אימות boot/recovery images
- יצירת דוחות בדיקה

**מחלקות עיקריות**:
```python
class TestResult(Enum):
    PASS, FAIL, WARNING, SKIP

@dataclass
class TestCase:
    name, description, result, message, details

class FirmwareTest:
    run_all_tests(partitions) -> List[TestCase]
    test_partition_sizes(partitions)
    test_boot_image(boot_path)
    get_test_report() -> str
```

---

### 6. GUI Components

#### Main Window (gui/main_window.py)
**תפקיד**: חלון ראשי ותאום בין רכיבים

**תכונות**:
- תפריטים וכלים
- ניהול לשוניות
- תזמון בדיקת מכשיר
- טיפול באירועים

#### Device Panel (gui/device_panel.py)
**תפקיד**: הצגת מידע על מכשיר מחובר

**מציג**:
- סטטוס חיבור
- מצב מכשיר
- דגם chip
- מידע טכני

#### Partition Panel (gui/partition_panel.py)
**תפקיד**: הצגת רשימת מחיצות

**מציג**:
- שם מחיצה
- גודל
- סוג
- סטטוס חילוץ
- Progress bar

#### Editor Panel (gui/editor_panel.py)
**תפקיד**: ממשק עריכה

**כולל**:
- Boot Logo Editor
- Build Properties Editor
- Modification Log

#### Preview Panel (gui/preview_panel.py)
**תפקיד**: תצוגה מקדימה חיה

**מציג**:
- סימולציה של מסך המכשיר
- Boot logo
- עדכונים בזמן אמת

---

## זרימת עבודה טיפוסית

```
1. Start Application
   └─> main.py
       └─> Load config.yaml
       └─> Setup logger
       └─> Create GUI

2. Detect Device
   └─> DeviceInterface.detect_device()
       └─> Check ADB
       └─> Check MTK USB
       └─> Get device info
       └─> Update DevicePanel

3. Extract Partitions
   └─> PartitionExtractor.read_partition_table()
       └─> Get partition list
       └─> Update PartitionPanel
   └─> PartitionExtractor.extract_all_partitions()
       └─> For each partition:
           └─> Read from device
           └─> Save to file
           └─> Update progress

4. Edit Firmware
   └─> FirmwareEditor.load_partition()
   └─> User makes changes:
       ├─> modify_boot_logo()
       ├─> modify_build_prop()
       └─> inject_file()
   └─> PreviewPanel updates

5. Test Firmware
   └─> FirmwareTest.run_all_tests()
       └─> Multiple test cases
       └─> Generate report
       └─> Display in log

6. Generate Scatter
   └─> ScatterFileGenerator.generate()
       └─> Create scatter file
       └─> Save to disk

7. Export Package
   └─> PackageExporter.create_flash_package()
       ├─> Copy all partitions
       ├─> Copy scatter file
       ├─> Generate checksums
       ├─> Create README
       └─> Create ZIP or folder

8. Flash with SP Flash Tool
   └─> User manually:
       ├─> Open SP Flash Tool
       ├─> Load scatter
       ├─> Connect device
       └─> Flash
```

---

## פרוטוקולים ותקשורת

### MTK Protocol
```
MTK devices communicate via USB in specific modes:

1. Preloader Mode (0x0e8d:0x0003)
   - First stage bootloader
   - Allows DRAM initialization
   - Low-level access

2. Download Mode (0x0e8d:0x2000, 0x201c)
   - Ready for firmware download
   - Partition read/write
   - Flash operations

Commands Structure:
[COMMAND_BYTE][LENGTH][DATA][CHECKSUM]
```

### ADB Protocol
```
Used when device is booted:
- List devices: adb devices
- Pull partition: adb pull /dev/block/{partition}
- Push files: adb push {file} /system/
- Shell access: adb shell
```

---

## פורמטים נתמכים

### Partition Images
- **Boot/Recovery**: Android boot image format (ANDROID! header)
- **System/Vendor**: ext4 filesystem images
- **Userdata/Cache**: ext4 or f2fs
- **Logo**: MTK custom logo format
- **Preloader**: Raw binary

### Scatter File
- Text format (UTF-8)
- YAML-like structure
- Contains partition mapping
- Used by SP Flash Tool

### Archive Packages
- ZIP format
- Contains all partitions
- Includes documentation
- MD5 checksums

---

## תלויות חיצוניות

### Python Packages
```
PyQt6          - GUI framework
pyserial       - Serial communication
pyusb          - USB device access
adb-shell      - ADB protocol
Pillow         - Image processing
python-magic   - File type detection
py7zr          - Archive compression
pyyaml         - Config parsing
```

### External Tools Required
```
SP Flash Tool  - Flashing firmware
MTK Drivers    - Device recognition
Python 3.8+    - Runtime environment
```

---

## אבטחה ושמירת מידע

### בטיחות
- ✅ שמירת גיבויים אוטומטית
- ✅ בדיקות תקינות לפני צריבה
- ✅ אימות checksums
- ✅ יומן שינויים מפורט

### סיכונים
- ⚠️ מחיקת מחיצות קריטיות
- ⚠️ צריבת קושחה לא תואמת
- ⚠️ ניתוק במהלך צריבה
- ⚠️ Hardbrick במקרים קיצוניים

---

## הרחבות עתידיות אפשריות

### תכונות מתקדמות
1. **עריכת Kernel**
   - Unpacking boot.img
   - Modifying kernel config
   - Repacking

2. **System.img Mounting**
   - Mount ext4 images
   - Direct file editing
   - App injection/removal

3. **OTA Package Creation**
   - Generate update.zip
   - Signature options
   - Incremental updates

4. **Multi-device Support**
   - Save device profiles
   - Quick switching
   - Batch operations

5. **Cloud Backup**
   - Upload firmware backups
   - Share custom ROMs
   - Version control

6. **Advanced Testing**
   - Boot simulation
   - Compatibility checks
   - Performance analysis

---

## פתרון בעיות נפוצות

### בעיות פיתוח

#### Import Errors
```python
# Problem: ModuleNotFoundError
# Solution:
pip install -r requirements.txt
python -m pip install --upgrade pip
```

#### USB Access Denied
```python
# Problem: usb.core.USBError: Access denied
# Solution (Windows):
# 1. Install MTK drivers
# 2. Run as Administrator
# 3. Check device in Device Manager
```

#### GUI Not Loading
```python
# Problem: PyQt6 errors
# Solution:
pip uninstall PyQt6
pip install PyQt6==6.5.0
```

---

## מסקנות

### מה בנינו
תוכנה מקצועית מלאה עם:
- ✅ 12+ מודולים פונקציונליים
- ✅ GUI מלא ואינטואיטיבי
- ✅ תמיכה במגוון פעולות
- ✅ בדיקות ואימות
- ✅ תיעוד מקיף

### טכנולוגיות
- Python (ליבה)
- PyQt6 (GUI)
- USB/Serial (תקשורת)
- Image Processing (עריכה)
- YAML (קונפיג)

### מתאים ל
- מפתחי ROM
- טכנאי תיקון
- חוקרים
- חובבי customization

---

**נוצר על ידי: MTK Firmware Editor Pro Development Team**
**גרסה: 1.0.0**
**תאריך: 2026**
