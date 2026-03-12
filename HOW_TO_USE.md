# איך להשתמש בתוכנה MTK Firmware Editor Pro

## 🚀 הפעלת התוכנה

### דרך 1: הפעלה ישירה מטרמינל
```powershell
cd "C:\path\to\project"
python main.py
```

### דרך 2: יצירת קיצור דרך
1. לחץ ימני על שולחן העבודה → חדש → קיצור דרך
2. מיקום:
   ```
   pythonw.exe "C:\path\to\project\main.py"
   ```
3. שם: MTK Firmware Editor Pro
4. סיום

---

## 🌐 בחירת שפה

### כאשר התוכנה פתוחה:

1. **חפש את התפריט העליון**
2. **לחץ על**: `Language / שפה / Langue`
3. **בחר אחת מהאפשרויות**:
   - `עברית (Hebrew)` - שפה עברית
   - `English` - אנגלית
   - `Français (French)` - צרפתית

4. **תופיע הודעה**: "Language changed to ..."
5. **לחץ OK**
6. **סגור את התוכנה**
7. **פתח מחדש**

### שינוי שפה ידני (בלי להפעיל):

```yaml
# ערוך את הקובץ: config.yaml

application:
  language: "he"   # שנה ל: "en" או "fr"
  
# דוגמאות:
  language: "he"   # עברית
  language: "en"   # English
  language: "fr"   # Français
```

שמור והפעל את התוכנה מחדש.

---

## 📱 זיהוי מכשיר Android

### אם המכשיר דלוק:

1. **הפעל USB Debugging** במכשיר:
   ```
   Settings → About Phone → 
   לחץ 7 פעמים על "Build Number"
   
   Settings → Developer Options →
   סמן "USB Debugging"
   ```

2. **חבר כבל USB** למחשב
3. **התר debugging** במכשיר (אם מופיע חלון)
4. **בתוכנה**: לחץ `זהה מכשיר` / `Detect Device`

### אם המכשיר כבוי או Brick:

#### שלב 1: התקן דרייברים (פעם אחת)

**אפשרות א': Zadig (מומלץ)**
```
1. הורד: https://zadig.akeo.ie
2. כבה את המכשיר
3. חבר USB למחשב
4. הפעל Zadig כמנהל
5. Options → List All Devices
6. בחר: MediaTek PreLoader / MTK USB Port
7. בחר Driver: WinUSB
8. לחץ Install Driver או Replace Driver
9. המתן להשלמה
```

**אפשרות ב': MTK Drivers**
```
1. חפש באינטרנט: "MediaTek VCOM Drivers"
2. הורד והתקן
3. הפעל מחדש את המחשב
```

#### שלב 2: הכנס למצב Preloader

**שיטה 1: מכשיר כבוי**
```
1. כבה את המכשיר
2. החזק: Volume Down
3. בזמן שאתה מחזיק - חבר USB
4. המכשיר צריך להיכנס ל-Preloader
```

**שיטה 2: מכשיר Brick**
```
1. נתק סוללה (אם ניתן)
2. חבר USB
3. חבר סוללה בחזרה
```

**שיטה 3: מקשים נוספים**
```
נסה אחת מהשילובים:
- Volume Up + Volume Down + USB
- Power + Volume Down + USB
- Volume Up + USB
```

#### שלב 3: זיהוי בתוכנה

1. **פתח MTK Firmware Editor Pro**
2. **לחץ `זהה מכשיר`**
3. **המערכת תזהה**:
   - מצב: Preloader / Download Mode
   - VID: 0e8d
   - PID: 0003 (Preloader) או 2000 (Download)

---

## 🔍 פתרון בעיות - מכשיר לא מזוהה

### בעיה 1: "No device found"

**פתרון:**
```powershell
# בדוק אם המכשיר נראה ב-Device Manager:
1. Win + X
2. Device Manager
3. חפש:
   - Ports (COM & LPT)
   - Universal Serial Bus controllers
   - Other Devices
   
אם יש סימן קריאה צהוב (!):
- לחץ ימני → Update Driver
- Browse my computer
- Let me pick → WinUSB או MTK
```

### בעיה 2: "Device in Error State"

**פתרון:**
```
1. התקן LibUSB/WinUSB (ראה למעלה)
2. נסה כבל USB אחר
3. נסה יציאת USB אחרת (אחורית - במחשב נייח)
4. נסה מצב אחר (Volume Up במקום Down)
```

### בעיה 3: "Unknown device" ב-Device Manager

**פתרון:**
```powershell
# בדוק VID:
Get-PnpDevice | Where-Object {$_.InstanceId -like '*VID_0E8D*'}

# אם מופיע:
Status: Error
→ צריך להתקין דרייבר

Status: OK
→ הדרייבר מותקן, התוכנה אמורה לזהות
```

---

## 🛠️ פעולות עיקריות

### 1. חילוץ מחיצות (Extract Partitions)

```
1. זהה מכשיר
2. לחץ "חלץ מחיצות" / "Extract Partitions"
3. בחר תיקיית יעד
4. המתן לסיום
5. המחיצות נשמרות כקבצי .img
```

### 2. יצירת קובץ Scatter

```
1. חלץ מחיצות (שלב 1)
2. לחץ "צור Scatter" / "Generate Scatter"
3. בחר שם ומיקום
4. הקובץ נוצר: MT_Android_scatter.txt
```

### 3. עריכת לוגו אתחול

```
1. חלץ מחיצות
2. עבור ללשונית "Editor"
3. לחץ "Select Logo Image"
4. בחר תמונה (PNG, JPG)
5. לחץ "Apply Logo"
```

### 4. ייצוא קושחה מעודכנת

```
1. ערוך שינויים (לוגו, properties)
2. לחץ "ייצא קושחה" / "Export Firmware"
3. בחר תיקיית יעד
4. הקבצים + Scatter נוצרים
5. השתמש ב-SP Flash Tool לפלאש
```

---

## 📊 הבנת ממשק התוכנה

### לשוניות (Tabs):

| לשונית | תיאור |
|--------|-------|
| **Device** | מידע על המכשיר המחובר |
| **Partitions** | רשימת מחיצות, סטטוס חילוץ |
| **Editor** | עריכת לוגו ו-Build Properties |
| **Preview** | תצוגה מקדימה של מסך אתחול |

### כפתורי Toolbar:

| כפתור | פעולה |
|-------|-------|
| `זהה מכשיר` | סריקת מכשירים מחוברים |
| `חלץ מחיצות` | חילוץ כל המחיצות מהמכשיר |
| `צור Scatter` | יצירת קובץ Scatter לפלאש |
| `ייצא קושחה` | ייצוא חבילת קושחה מלאה |

---

## ⚡ טיפים חשובים

### כבל USB:
- ✅ השתמש בכבל **מקורי**
- ✅ ודא שהכבל תומך ב-**Data** (לא רק טעינה)
- ✅ נסה **כבל קצר** (עד 1 מטר)

### יציאת USB:
- ✅ יציאה **אחורית** (במחשב נייח) - יותר יציבה
- ✅ יציאה **ישירה** (לא דרך Hub)
- ✅ **USB 2.0** עובד יותר טוב מ-3.0 למכשירי MTK

### סביבת עבודה:
- ✅ סגור **תוכנות אנטי וירוס** זמנית
- ✅ הרץ את התוכנה **כמנהל** (אם צריך)
- ✅ אל תנתק את המכשיר **בזמן חילוץ**

---

## 📁 מבנה תיקיות לאחר עבודה

```
C:\path\to\project\
│
├── extracted_partitions/      # מחיצות שחולצו
│   ├── boot.img
│   ├── system.img
│   ├── recovery.img
│   └── ...
│
├── output/                    # קושחה מוכנה לפלאש
│   ├── boot.img
│   ├── system.img
│   ├── MT_Android_scatter.txt
│   └── ...
│
└── logs/                      # קבצי לוג
    ├── mtk_editor_2025-03-08.log
    └── ...
```

---

## 🎯 תרחישים נפוצים

### תרחיש 1: שינוי לוגו אתחול
```
1. חבר מכשיר → זהה
2. חלץ מחיצות
3. Editor → Select Logo → בחר תמונה
4. Apply Logo
5. Export Firmware
6. פלאש עם SP Flash Tool
```

### תרחיש 2: שחזור מכשיר Brick
```
1. התקן Zadig drivers
2. חבר מכשיר כבוי + Volume Down
3. זהה מכשיר (Preloader mode)
4. חלץ מחיצות
5. שמור גיבוי!
```

### תרחיש 3: שינוי Build Properties
```
1. חבר → זהה → חלץ
2. Editor → Build Properties
3. הזן:
   ro.product.model=My Phone
   ro.build.display.id=Custom ROM
4. Apply Properties
5. Export → Flash
```

---

## 📞 קבלת עזרה

### קבצי עזרה:
- `README.md` - מידע כללי
- `USER_GUIDE.md` - מדריך מפורט
- `QUICK_START.md` - התחלה מהירה
- `LIBUSB_SETUP_GUIDE.md` - התקנת דרייברים
- `LANGUAGE_USAGE_GUIDE.md` - מדריך שפות

### לוגים:
```powershell
# צפה בלוג אחרון:
Get-Content logs\mtk_editor_*.log | Select-Object -Last 50
```

---

## ✅ צ'קליסט לפני שימוש

- [ ] Python 3.14 מותקן
- [ ] כל התלויות מותקנות (`pip install -r requirements.txt`)
- [ ] MTK/LibUSB drivers מותקנים
- [ ] כבל USB תקין
- [ ] USB Debugging מופעל (אם מכשיר דלוק)
- [ ] התוכנה נפתחת ללא שגיאות
- [ ] תפריט Language נראה
- [ ] ניתן לשנות שפה

---

**בהצלחה! 🚀**

אם יש בעיות, בדוק את קבצי הלוג בתיקייה `logs/`
