# הדרכת התקנת LibUSB לזיהוי מכשירים כבויים/Brick

## למה צריך LibUSB?

כדי לזהות מכשירי MTK במצבים מיוחדים (כבוי, brick, preloader), צריך להתקין דרייבר LibUSB.

---

## התקנה באמצעות Zadig (מומלץ)

### שלב 1: הורד Zadig
1. גלוש אל: **https://zadig.akeo.ie/**
2. הורד את **zadig.exe**
3. אל צריך התקנה - זה קובץ נייד

### שלב 2: הכן את המכשיר
```
1. כבה את המכשיר המכשיר לחלוטין
2. חבר למחשב דרך USB
   (או החזק Power + Volume Down תוך כדי חיבור)
3. המכשיר אמור להיכנס למצב MTK Preloader/Download
```

### שלב 3: התקן דרייבר
1. **הפעל Zadig כמנהל** (Run as Administrator)
2. לחץ על **Options** → בחר **List All Devices**
3. בתפריט, חפש אחד מאלה:
   - `MediaTek PreLoader USB VCOM`
   - `MTK USB Port`
   - `Android`
   - או כל התקנה עם `VID: 0E8D`

4. בחר את ההתקנה

5. בחר דרייבר:
   - אם כתוב `(NONE)` → בחר **WinUSB** או **libusb-win32**
   - אם כתוב דרייבר אחר → לחץ **Replace Driver**

6. לחץ **Install Driver** או **Replace Driver**

7. המתן לסיום ההתקנה (כ-30 שניות)

8. סגור את Zadig

### שלב 4: אמת
```powershell
# פתח PowerShell ובדוק:
Get-PnpDevice | Where-Object {$_.InstanceId -like '*VID_0E8D*'}
```

אם הצלחת, אמור להופיע משהו כמו:
```
Status: OK
FriendlyName: MediaTek PreLoader USB VCOM (WinUSB)
```

---

## שיטה חלופית: MTK Drivers רשמיים

### אם Zadig לא עובד:

1. **הורד MTK USB Drivers:**
   - חפש: "MediaTek VCOM Drivers"
   - או: "MTK Preloader USB Driver"

2. **התקן:**
   ```
   - חלץ את הקבצים
   - הפעל Install.bat כמנהל
   - עקוב אחר ההוראות
   ```

3. **הפעל מחדש** את המחשב

---

## פתרון בעיות

### בעיה: Zadig לא רואה את המכשיר

**פתרון:**
```
1. ודא שהמכשיר מחובר ובמצב Download/Preloader
2. ב-Zadig: Options → List All Devices
3. נתק וחבר מחדש את המכשיר
4. נסה יציאת USB אחרת
```

### בעיה: "Driver Installation Failed"

**פתרון:**
```
1. כבה Secure Boot ב-BIOS
2. ב-Windows: Settings → Update & Security → For Developers
   → בחר "Developer Mode"
3. נסה שוב להתקין
```

### בעיה: Windows אומר "Driver Signature"

**פתרון:**
```powershell
# הפעל PowerShell כמנהל:
bcdedit /set testsigning on
# הפעל מחדש את המחשב
# אחרי התקנת הדרייבר, ניתן לכבות:
bcdedit /set testsigning off
```

### בעיה: עדיין לא מזהה

**בדוק:**
```powershell
# בדוק אם המכשיר מופיע בכלל:
Get-PnpDevice | Where-Object {$_.Status -eq 'Error' -or $_.Status -eq 'Unknown'}
```

אם רואה משהו עם `VID_0E8D`:
- המכשיר מחובר אבל הדרייבר לא תקין
- נסה להתקין מחדש עם Zadig

---

## בדיקה סופית

### אחרי התקנת הדרייברים:

1. **חבר מכשיר כבוי** למחשב
2. **הפעל את התוכנה MTK Firmware Editor Pro**
3. לחץ **"Detect Device"**
4. אמור להופיע:
   ```
   Device detected: Preloader / Download Mode / Brick
   ```

---

## עזרה נוספת

### אם כלום לא עובד:

1. **בדוק Device Manager:**
   ```
   Win + X → Device Manager
   - חפש: Ports (COM & LPT)
   - חפש: Universal Serial Bus devices
   - חפש: Android Phone / MediaTek
   ```

2. **אם רואה סימן קריאה צהוב (!)**:
   ```
   - לחץ ימני → Update Driver
   - Browse my computer for drivers
   - Let me pick from available drivers
   - בחר MTK או WinUSB
   ```

3. **לוג של התוכנה:**
   ```
   תיקייה: logs/
   פתח את הקובץ האחרון וחפש שגיאות
   ```

---

## טיפים חשובים

✅ **שימוש ב-Zadig - בחר WinUSB**
   - עובד הכי טוב עם PyUSB (ספרייה שהתוכנה משתמשת בה)

✅ **כבל USB איכותי**
   - כבל פגום יכול לגרום לזיהוי לא יציב

✅ **יציאת USB אחורית** (במחשב נייח)
   - לעיתים יציאות קדמיות לא מספקות מספיק חשמל

✅ **נסה מצבים שונים:**
   ```
   מצב 1: מכשיר כבוי + חיבור USB
   מצב 2: החזק Volume Down + חבר USB
   מצב 3: החזק Volume Up + Volume Down + חבר USB
   ```

---

## סיכום

הצעדים העיקריים:
1. ✅ הורד Zadig
2. ✅ חבר מכשיר במצב Download/Preloader
3. ✅ התקן WinUSB driver דרך Zadig
4. ✅ בדוק זיהוי בתוכנה

**מזל טוב! המכשיר שלך אמור להיות מזוהה כעת גם במצב כבוי או brick! 🎉**
