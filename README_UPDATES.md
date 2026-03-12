# עדכונים חדשים למערכת MTK Firmware Editor Pro

## 🌍 תמיכה רב-לשונית (Multi-Language Support)

המערכת תומכת כעת ב-**3 שפות מלאות**:

### שפות נתמכות:
1. **עברית (Hebrew)** - שפת ברירת מחדל
2. **English** - אנגלית
3. **Français (French)** - צרפתית

### כיצד לשנות שפה:
```
1. פתח את התוכנה
2. לחץ על תפריט "Language / שפה / Langue"
3. בחר שפה:
   - עברית (Hebrew)
   - English
   - Français (French)
4. אשר את השינוי
5. הפעל מחדש את התוכנה
```

### תכונות רב-לשוניות:
- ✅ כל ממשק המשתמש מתורגם
- ✅ תפריטים, כפתורים, הודעות
- ✅ דיאלוגים ושגיאות
- ✅ תמיכה ב-RTL (עברית)
- ✅ תמיכה ב-LTR (אנגלית, צרפתית)
- ✅ שמירת העדפות בקובץ תצורה

---

## 📱 זיהוי מכשירים מתקדם (Enhanced Device Detection)

### תמיכה במכשירים כבויים ו-Bricked:

המערכת כעת מזהה מכשירי MTK **גם כאשר הם כבויים או במצב Brick**!

### שיטות זיהוי:
1. **Windows Device Manager** - סריקת התקנים במערכת
2. **USB VID/PID Scanning** - זיהוי ישיר של חומרה
3. **ADB Detection** - זיהוי מכשירים ב-ADB

### PIDs נתמכים:
- `0e8d:0003` - MTK Preloader Mode
- `0e8d:2000` - MTK Download Mode
- `0e8d:201c` - MTK Download Mode (Alternative)
- `0e8d:2008` - MTK Normal Mode

### מצבים מזוהים:
- ✅ **Powered On** - מכשיר דלוק ועובד
- ✅ **Preloader** - מצב preloader (מוכן לפלאש)
- ✅ **Download Mode** - מצב הורדה (SP Flash Tool ready)
- ✅ **Brick/Recovery** - מכשיר Brick או במצב שחזור

### הודעות עזרה:
כאשר מכשיר לא מזוהה, המערכת מציגה:
- 🔍 זיהוי מכשירים שגויים/Brick
- 💡 הצעות לפתרונות
- 🔧 הדרכה להתקנת דרייברים

---

## 🛠️ דרייברים נדרשים

### עבור זיהוי מכשירים כבויים/Brick:

#### Windows:
```powershell
# הגדר התקן כ-WinUSB באמצעות Zadig:
1. הורד Zadig מ-https://zadig.akeo.ie
2. חבר מכשיר במצב preloader (כבוי + USB)
3. הפעל Zadig כמנהל
4. Options → List All Devices
5. בחר MTK Preloader/MediaTek
6. בחר WinUSB driver
7. לחץ Install Driver
```

#### קבצי מדריך:
- **LIBUSB_SETUP_GUIDE.md** - מדריך מפורט להתקנת LibUSB/WinUSB
- **LANGUAGE_USAGE_GUIDE.md** - מדריך שימוש בשפות

---

## 📂 קבצים חדשים

### תרגומים:
```
translations/
├── en.yaml  # English translations (150+ strings)
├── he.yaml  # Hebrew translations (150+ strings)
└── fr.yaml  # French translations (150+ strings)
```

### מודולים:
```
utils/
└── i18n.py  # Internationalization manager

core/
└── enhanced_detector.py  # Enhanced device detection
```

### תיעוד:
```
LANGUAGE_USAGE_GUIDE.md    # מדריך שפות
LIBUSB_SETUP_GUIDE.md      # מדריך LibUSB
README_UPDATES.md          # קובץ זה
```

---

## 🔧 שינויים טכניים

### gui/main_window.py:
- ✅ אתחול מערכת i18n
- ✅ אתחול Enhanced Detector
- ✅ תפריט Language עם 3 שפות
- ✅ פונקציית `change_language()`
- ✅ עדכון `detect_device()` עם Enhanced Detection
- ✅ תרגום כל הכפתורים והודעות
- ✅ תרגום Toolbar
- ✅ תרגום דיאלוגים

### main.py:
- ✅ טעינת i18n במערכת
- ✅ קריאת שפה מקובץ הגדרות
- ✅ הגדרת שפת ברירת מחדל

### config.yaml:
```yaml
application:
  language: "he"  # Hebrew default
```

---

## 🚀 כיצד להשתמש

### זיהוי מכשיר כבוי/Brick:

```
1. כבה את המכשיר לחלוטין
2. חבר כבל USB למחשב
3. פתח את MTK Firmware Editor Pro
4. לחץ "זהה מכשיר" / "Detect Device"
5. המערכת תזהה את המכשיר אוטומטית
```

### אם המכשיר לא מזוהה:
```
1. וודא שדרייברי MTK מותקנים
2. התקן LibUSB/WinUSB (ראה LIBUSB_SETUP_GUIDE.md)
3. נסה מצבים שונים:
   - Volume Down + חיבור USB
   - Volume Up + Volume Down + חיבור USB
4. בדוק כבל USB
5. נסה יציאת USB אחרת
```

---

## 📊 סטטיסטיקות

### קוד:
- **קבצי תרגום**: 3 קבצים (450+ שורות סה"כ)
- **מחרוזות מתורגמות**: 150+ לכל שפה
- **שיטות זיהוי**: 3 (WDM, USB, ADB)
- **PIDs נתמכים**: 4 מצבי MTK

### תכונות:
- ✅ תמיכה ב-3 שפות
- ✅ זיהוי מכשירים כבויים
- ✅ זיהוי מצבי Brick
- ✅ הודעות שגיאה מפורטות
- ✅ הדרכה להתקנת דרייברים
- ✅ שמירת העדפות שפה

---

## 🔮 תכונות עתידיות

### בתכנון:
- [ ] תמיכה בשפות נוספות (ספרדית, סינית, רוסית)
- [ ] זיהוי אוטומטי של שפת מערכת
- [ ] עדכון דינמי של ממשק ללא Restart
- [ ] תמיכה ב-Qualcomm EDL mode
- [ ] תמיכה ב-Samsung Odin mode
- [ ] ממשק API לתוספים (plugins)

---

## 📸 צילומי מסך

### תפריט שפות:
```
┌─────────────────────────┐
│ Language / שפה / Langue │
├─────────────────────────┤
│ → עברית (Hebrew)        │
│   English               │
│   Français (French)     │
└─────────────────────────┘
```

### הודעת זיהוי מכשיר:
```
╔═══════════════════════════════╗
║  מכשיר זוהה / Device Detected ║
╠═══════════════════════════════╣
║  מצב: Preloader               ║
║  מכשיר: MediaTek MT6765       ║
║  VID: 0e8d                    ║
║  PID: 0003                    ║
╚═══════════════════════════════╝
```

### הודעת Brick:
```
⚠️ מכשיר במצב שגיאה / Device in Error State

זוהה מכשיר MTK אך נראה שהוא במצב Brick.

פתרונות:
1. התקן MTK USB VCOM drivers
2. התקן libusb/WinUSB (Zadig)
3. נסה מצב Preloader
```

---

## 🎉 סיכום

### השינויים הדרמטיים הוטמעו בהצלחה!

- ✅ **תמיכה ב-3 שפות מלאות**
- ✅ **זיהוי מכשירים כבויים/Brick**
- ✅ **Enhanced Device Detection**
- ✅ **הודעות מפורטות ועזרה**
- ✅ **תיעוד מלא**

התוכנה כעת מסוגלת:
1. לזהות מכשירי MTK **גם כשהם כבויים**
2. לזהות מכשירים **במצב Brick**
3. לספק **הדרכה מפורטת** למשתמש
4. לעבוד ב-**3 שפות שונות**
5. לשמור **העדפות משתמש**

**הכל עובד ומוכן לשימוש! 🚀**

---

## 📞 עזרה ותמיכה

- **מדריך שפות**: [LANGUAGE_USAGE_GUIDE.md](LANGUAGE_USAGE_GUIDE.md)
- **מדריך LibUSB**: [LIBUSB_SETUP_GUIDE.md](LIBUSB_SETUP_GUIDE.md)
- **מדריך מהיר**: [QUICK_START.md](QUICK_START.md)
- **מדריך משתמש**: [USER_GUIDE.md](USER_GUIDE.md)

---

**גרסה: 1.1.0**  
**תאריך עדכון: 2025**  
**מפתח: AI Assistant + User MH**
