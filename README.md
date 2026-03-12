# MTK Firmware Editor Pro

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-Educational-orange)

תוכנה מתקדמת לעריכת קושחות אנדרואיד עבור מכשירי MediaTek.

## תכונות עיקריות

### 🔌 חיבור למכשיר
- זיהוי אוטומטי של מכשירי MTK
- תמיכה במצבים שונים: ADB, Fastboot, MTK Preloader, MTK Download Mode
- יכולת גישה למכשירים גם כשהם לא נדלקים

### 💾 חילוץ מחיצות (Partitions)
- חילוץ אוטומטי של כל מחיצות המכשיר
- תמיכה במחיצות סטנדרטיות: preloader, boot, system, recovery, ועוד
- שמירת קבצי תמונה (image files) של כל מחיצה

### ✏️ עריכת קושחה
- **שינוי לוגו אתחול (Boot Logo)**: החלף את תמונת האתחול של המכשיר
- **עריכת Build Properties**: שנה מאפייני מערכת כמו שם מכשיר, גירסת אנדרואיד, ועוד
- **הזרקת קבצים**: הוסף קבצים מותאמים אישית למחיצות המערכת
- יומן שינויים מפורט

### 📱 תצוגה מקדימה חיה
- סימולציה של מסך אנדרואיד
- תצוגה של שינויים בזמן אמת
- תצוגה של לוגו אתחול מותאם

### 📄 יצירת קובץ Scatter
- יצירה אוטומטית של קבצי Scatter עבור SP Flash Tool
- תמיכה בפורמט MTK הסטנדרטי
- עדכון אוטומטי של כתובות ו גדלים

### ✅ בדיקות ואימות
- מערכת בדיקות מקיפה לאימות שינויים
- בדיקת תקינות מחיצות
- אימות מבנה של boot images
- יצירת דוח בדיקות מפורט

### 📦 ייצוא חבילה לצריבה
- יצירת חבילת קושחה מלאה מוכנה לצריבה
- כולל קבצי scatter, partitions, והוראות התקנה
- תמיכה בפורמט ZIP או תיקייה
- קובץ checksums לאימות תקינות

## דרישות מערכת

### תוכנה נדרשת
- Python 3.8 ואילך
- Windows 10/11
- SP Flash Tool (להורדה נפרדת)
- MTK USB Drivers

### חומרה נדרשת
- מחשב Windows
- כבל USB איכותי
- מכשיר אנדרואיד מבוסס MTK chipset

## התקנה

### 1. התקן Python
הורד והתקן Python 3.8+ מ-https://python.org

### 2. התקן תלויות
```powershell
cd "C:\path\to\project"
pip install -r requirements.txt
```

### 3. התקן MTK Drivers
הורד והתקן MTK USB drivers עבור המכשיר שלך

### 4. הכן SP Flash Tool
הורד את SP Flash Tool מהאתר הרשמי של MediaTek

## שימוש בתוכנה

### הפעלה
```powershell
python main.py
```

### תהליך עבודה בסיסי

#### 1. חיבור מכשיר
- חבר את מכשיר ה-Android למחשב
- לחץ על "Detect Device"
- התוכנה תזהה את המכשיר ואת מצבו

#### 2. חילוץ קושחה
- בחר תיקיית עבודה
- לחץ על "Extract Partitions"
- המתן לסיום חילוץ כל המחיצות

#### 3. עריכת קושחה
- בלשונית "Editor", בחר את השינויים הרצויים:
  - **שינוי לוגו**: העלה תמונה PNG/JPG/BMP
  - **מאפיינים**: ערוך build.prop properties
- צפה בשינויים בלשונית "Live Preview"

#### 4. בדיקת שינויים
- התוכנה תריץ בדיקות אוטומטיות
- בדוק דוח בדיקות ביומן (Log tab)

#### 5. יצירת Scatter File
- Tools → Generate Scatter File
- שמור את הקובץ בתיקיית הפלט

#### 6. ייצוא חבילה
- Tools → Export Modified Firmware
- בחר תיקיית יעד
- התוכנה תיצור חבילה מלאה עם הוראות

#### 7. צריבה למכשיר
- פתח את SP Flash Tool
- טען את קובץ ה-Scatter שנוצר
- עקוב אחר ההוראות ב-FLASH_INSTRUCTIONS.txt

## מבנה הפרויקט

```
MTK_Firmware_Editor/
├── main.py                 # Entry point
├── config.yaml            # Configuration
├── requirements.txt       # Dependencies
├── README.md             # Documentation (this file)
│
├── core/                 # Core modules
│   ├── device_interface.py      # Device communication
│   ├── partition_extractor.py   # Partition extraction
│   ├── scatter_generator.py     # Scatter file generator
│   ├── firmware_editor.py       # Firmware editor
│   ├── firmware_test.py         # Testing framework
│   └── config_manager.py        # Config management
│
├── gui/                  # GUI components
│   ├── main_window.py           # Main window
│   ├── device_panel.py          # Device info panel
│   ├── partition_panel.py       # Partition list panel
│   ├── editor_panel.py          # Editor interface
│   └── preview_panel.py         # Live preview
│
└── utils/                # Utilities
    ├── logger.py                # Logging setup
    └── package_exporter.py      # Package export
```

## אזהרות חשובות ⚠️

### סיכונים
- **צריבת קושחה יכולה לגרום נזק קבוע למכשיר (bricking)**
- **אובדן אחריות**
- **אובדן מידע**

### המלצות בטיחות
1. **תמיד צור גיבוי** של הקושחה המקורית לפני שינויים
2. **ודא התאמה** - השתמש רק בקושחה מתאימה למכשיר שלך
3. **סוללה טעונה** - ודא שהסוללה טעונה לפחות 50%
4. **כבל איכותי** - השתמש בכבל USB מקורי ואיכותי
5. **אל תנתק** - אף פעם אל תנתק את המכשיר במהלך הצריבה

### אחריות משפטית
- תוכנה זו מיועדת למטרות חינוכיות ומחקר בלבד
- המפתחים אינם אחראים לכל נזק שייגרם למכשיר או למידע
- השימוש בתוכנה הוא על אחריות המשתמש בלבד

## פתרון בעיות

### המכשיר לא מזוהה
- התקן MTK USB drivers
- נסה יציאת USB אחרת
- הפעל מחדש את המכשיר למצב download mode

### שגיאה בחילוץ מחיצות
- ודא שהמכשיר במצב התקין
- בדוק חיבור USB
- נסה להפעיל מחדש את התוכנה

### בעיות בצריבה
- ודא תאימות קובץ scatter למכשיר
- בדוק MD5 checksums
- השתמש בגרסה עדכנית של SP Flash Tool

## תכונות מתקדמות

### עריכת מחיצות ישירות
```python
from core.firmware_editor import FirmwareEditor

editor = FirmwareEditor(config)
editor.inject_file('system', 'myapp.apk', '/system/app/myapp.apk')
```

### בדיקות מותאמות אישית
```python
from core.firmware_test import FirmwareTest

tester = FirmwareTest(config)
results = tester.run_all_tests(partitions)
print(tester.get_test_report())
```

## תמיכה טכנית

תוכנה זו היא פרויקט קוד פתוח ללא תמיכה רשמית.

## רישיון

תוכנה זו מיועדת למטרות חינוכיות ומחקר בלבד.

## תודות

- SP Flash Tool by MediaTek
- Python community
- Open source contributors

---

**שימו לב**: תוכנה זו מיועדת למשתמשים מתקדמים בלבד. אם אינך בטוח במה שאתה עושה, אל תשתמש בתוכנה זו!
