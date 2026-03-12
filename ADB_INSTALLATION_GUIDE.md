# התקנת ADB (Android Debug Bridge) - מדריך מלא

## 🔧 מה זה ADB ולמה צריך אותו?

**ADB (Android Debug Bridge)** הוא כלי שמאפשר תקשורת עם מכשיר Android דלוק.

### מתי צריך ADB:
- ✅ מכשיר Android דלוק עם USB Debugging
- ✅ קריאת מידע מהמכשיר
- ✅ הרצת פקודות על המכשיר
- ✅ גישה למחיצות (אם יש Root)

### מתי לא צריך ADB:
- ❌ מכשיר כבוי במצב Preloader
- ❌ מכשיר במצב Download Mode (SP Flash Tool)
- ❌ מכשיר Brick

---

## 📥 שיטה 1: התקנה מהירה (Platform Tools)

### Windows:

#### שלב 1: הורדה
```
1. גלוש ל: https://developer.android.com/tools/releases/platform-tools
2. לחץ על "Download SDK Platform-Tools for Windows"
3. אשר את התנאים
4. הורד את הקובץ (platform-tools-latest-windows.zip)
```

#### שלב 2: חילוץ
```powershell
# צור תיקייה:
New-Item -Path "C:\Android" -ItemType Directory -Force

# חלץ את הקובץ ל:
C:\Android\platform-tools\
```

#### שלב 3: הוספה ל-PATH
```powershell
# הפעל PowerShell כמנהל והרץ:
[Environment]::SetEnvironmentVariable(
    "Path",
    [Environment]::GetEnvironmentVariable("Path", "Machine") + ";C:\Android\platform-tools",
    "Machine"
)
```

#### שלב 4: אימות
```powershell
# סגור ופתח PowerShell חדש
# בדוק:
adb version

# אמור להופיע:
# Android Debug Bridge version 1.0.41
# Version 34.0.x...
```

---

## 📥 שיטה 2: התקנה דרך Chocolatey (מומלץ)

### אם יש לך Chocolatey:
```powershell
# הפעל PowerShell כמנהל:
choco install adb

# או התקנת tools מלא:
choco install android-sdk
```

### אם אין Chocolatey:
```powershell
# התקן Chocolatey קודם:
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# ואז:
choco install adb
```

---

## 🔧 הפעלת USB Debugging במכשיר

### שלב 1: הפעל Developer Options

**Android 4.2 ומעלה:**
```
1. Settings → About Phone
2. לחץ 7 פעמים על "Build Number"
3. תראה הודעה: "You are now a developer!"
```

**Xiaomi (MIUI):**
```
1. Settings → About Phone → MIUI Version
2. לחץ 7 פעמים על "MIUI Version"
```

**Samsung:**
```
1. Settings → About Phone → Software Information
2. לחץ 7 פעמים על "Build Number"
```

### שלב 2: הפעל USB Debugging
```
1. Settings → System → Developer Options
   (או: Settings → Additional Settings → Developer Options)

2. סמן:
   ☑ USB Debugging
   ☑ Install via USB (אופציונלי)

3. אשר את ההתרעה
```

---

## 🔌 חיבור המכשיר

### שלב 1: חבר USB
```
1. חבר כבל USB למכשיר ולמחשב
2. בחר במכשיר: "File Transfer" או "MTP"
   (לא "Charge Only")
```

### שלב 2: אשר Debugging
```
במכשיר יופיע חלון:
"Allow USB debugging?"

☑ Always allow from this computer
→ OK
```

### שלב 3: בדוק חיבור
```powershell
adb devices

# אמור להופיע:
List of devices attached
ABC123456789    device
```

---

## 🛠️ פתרון בעיות

### בעיה: "adb לא מזוהה"

**פתרון:**
```powershell
# בדוק PATH:
$env:Path -split ';' | Select-String "platform-tools"

# אם לא רואה, הוסף ידנית:
# Control Panel → System → Advanced → Environment Variables
# Path → Edit → New → C:\Android\platform-tools
```

### בעיה: "no devices/emulators found"

**פתרון 1: הפעל מחדש ADB**
```powershell
adb kill-server
adb start-server
adb devices
```

**פתרון 2: בדוק דרייברים**
```
1. Win + X → Device Manager
2. חפש: "Android Device" או שם המכשיר
3. אם יש סימן קריאה (!) → Update Driver

או התקן דרייברים:
- Google USB Driver: https://developer.android.com/studio/run/win-usb
- דרייבר היצרן (Samsung, Xiaomi, וכו')
```

**פתרון 3: נסה כבל אחר**
```
כבלים רבים הם "Charge Only"
צריך כבל שתומך ב-Data
```

### בעיה: "unauthorized"

**פתרון:**
```
1. נתק USB
2. במכשיר: Settings → Developer Options
   → Revoke USB debugging authorizations
3. חבר מחדש
4. אשר מחדש את ההודעה (סמן Always allow)
```

### בעיה: "offline"

**פתרון:**
```powershell
# הפעל מחדש ADB:
adb kill-server
adb start-server

# או הפעל מחדש את המכשיר
```

---

## ✅ בדיקה סופית

### אחרי התקנת ADB:

```powershell
# 1. בדוק גרסה:
adb version

# 2. בדוק מכשירים:
adb devices

# אמור להופיע:
List of devices attached
ABC123456789    device

# 3. קבל מידע מהמכשיר:
adb shell getprop ro.product.model
adb shell getprop ro.build.version.release
```

### עכשיו נסה את התוכנה:
```powershell
cd "C:\path\to\project"
python main.py

# לחץ "זהה מכשיר" / "Detect Device"
# המכשיר אמור להיזהות!
```

---

## 📊 פקודות ADB שימושיות

### קבלת מידע:
```powershell
adb devices -l                    # רשימה מפורטת
adb shell getprop                 # כל המאפיינים
adb shell df                      # שימוש בדיסק
adb shell dumpsys battery         # סטטוס סוללה
```

### פעולות:
```powershell
adb reboot                        # הפעלה מחדש
adb reboot recovery               # אתחול ל-Recovery
adb reboot bootloader             # אתחול ל-Bootloader/Fastboot
adb reboot edl                    # אתחול ל-EDL (Qualcomm)
```

### קבצים:
```powershell
adb push file.txt /sdcard/        # העתקה למכשיר
adb pull /sdcard/file.txt .       # העתקה מהמכשיר
```

---

## 🚀 שילוב עם התוכנה

### לאחר התקנת ADB:

**התוכנה תזהה אוטומטית מכשירים דלוקים:**

```
1. הפעל USB Debugging במכשיר
2. חבר USB למחשב
3. אשר את ה-Debugging prompt
4. פתח את MTK Firmware Editor Pro
5. לחץ "זהה מכשיר"
→ המכשיר יזוהה במצב ADB
```

**אם המכשיר במצב Preloader/Download:**
```
לא צריך ADB!
המערכת תזהה דרך LibUSB/WinUSB
```

---

## 💡 טיפים

### 1. שמור את platform-tools במיקום קבוע
```
✅ טוב: C:\Android\platform-tools
❌ רע: C:\Users\<username>\Downloads\platform-tools-34\
```

### 2. הוסף לסביבה גלובלית
```
כך תוכל להשתמש ב-adb מכל מקום
```

### 3. עדכן מדי פעם
```powershell
# הורד גרסה חדשה מהאתר
# או עם Chocolatey:
choco upgrade adb
```

### 4. אם יש בעיות עם דרייברים
```
התקן Google USB Driver:
https://developer.android.com/studio/run/win-usb

או השתמש ב-Universal ADB Driver:
https://adb.clockworkmod.com/
```

---

## 🔗 קישורים שימושיים

- **Platform Tools (רשמי):** https://developer.android.com/tools/releases/platform-tools
- **Google USB Driver:** https://developer.android.com/studio/run/win-usb
- **Universal ADB Driver:** https://adb.clockworkmod.com/
- **XDA ADB Tutorial:** https://www.xda-developers.com/install-adb-windows-macos-linux/

---

## 📞 עזרה נוספת

### אם עדיין לא עובד:

1. **בדוק לוגים:**
```powershell
# הפעל עם verbose:
adb logcat

# או בדוק את לוג התוכנה:
Get-Content logs\mtk_editor_*.log | Select-Object -Last 100
```

2. **נסה עם כלי אחר:**
```
Minimal ADB and Fastboot: https://androidmtk.com/download-minimal-adb-and-fastboot-tool
```

3. **בדוק אנטי-וירוס:**
```
חלק מתוכנות אנטי-וירוס חוסמות ADB
נסה להוסיף חריגה ל-adb.exe
```

---

**אחרי התקנת ADB, התוכנה תזהה מכשירים דלוקים מיד! 🚀**
