# מדריך שימוש - תמיכה רב-לשונית

## התוכנה תומכת כעת ב-3 שפות!

### 🌐 **שפות זמינות:**
1. **עברית (HE)** - שפת ברירת מחדל
2. **English (EN)** - אנגלית
3. **Français (FR)** - צרפתית

---

## איך לשנות שפה?

### דרך 1: תפריט Language
```
1. פתח את התוכנה
2. לחץ על תפריט "Language / שפה / Langue"
3. בחר את השפה הרצויה:
   - עברית (Hebrew)
   - English
   - Français (French)
4. לחץ OK בחלון האישור
5. סגור והפעל מחדש את התוכנה
```

### דרך 2: ערוך את קובץ config.yaml
```yaml
# פתח את הקובץ: config.yaml
# חפש את השורה:
application:
  language: "he"  # שינוי ל: "en" או "fr"
  
# דוגמאות:
  language: "he"  # עברית
  language: "en"  # English
  language: "fr"  # Français

# שמור וסגור
# הפעל מחדש את התוכנה
```

---

## השוואת שפות

### **דוגמה 1: כפתורי Toolbar**

| עברית | English | Français |
|-------|---------|----------|
| זהה מכשיר | Detect Device | Détecter l'appareil |
| חלץ מחיצות | Extract Partitions | Extraire les partitions |
| צור Scatter | Generate Scatter | Générer Scatter |
| ייצא קושחה | Export Firmware | Exporter le firmware |

### **דוגמה 2: תפריט File**

| עברית | English | Français |
|-------|---------|----------|
| חדש | New | Nouveau |
| פתח | Open | Ouvrir |
| שמור | Save | Enregistrer |
| יציאה | Exit | Quitter |

### **דוגמה 3: הודעות**

**זוהה מכשיר:**
- **עברית:** "מכשיר זוהה: Preloader"
- **English:** "Device detected: Preloader"
- **Français:** "Appareil détecté : Preloader"

**מכשיר במצב Brick:**
- **עברית:** "זוהה מכשיר MTK אך נראה שהוא במצב שגיאה או Brick..."
- **English:** "An MTK device was detected but appears to be in an error or brick state..."
- **Français:** "Un appareil MTK a été détecté mais semble être dans un état d'erreur ou brick..."

---

## תמיכה ב-RTL (עברית)

כאשר תבחר בעברית, הממשק יתאים אוטומטית:
- ✅ טקסט מימין לשמאל
- ✅ תפריטים בעברית
- ✅ כפתורים בעברית
- ✅ הודעות שגיאה בעברית
- ✅ דיאלוגים בעברית

---

## הוספת שפה חדשה

אם ברצונך להוסיף שפה נוספת:

### שלב 1: צור קובץ תרגום
```bash
# העתק קובץ תבנית
copy translations/en.yaml translations/es.yaml  # לדוגמה: ספרדית
```

### שלב 2: ערוך את הקובץ
```yaml
# translations/es.yaml
language:
  name: "Español"
  code: "es"
  direction: "ltr"

app:
  name: "Editor de Firmware MTK Pro"
  
menu:
  file: "Archivo"
  edit: "Editar"
  # ... המשך תרגום
```

### שלב 3: הוסף לקוד
```python
# gui/main_window.py
# בתוך create_menu_bar, הוסף:
spanish_action = QAction("Español", self)
spanish_action.triggered.connect(lambda: self.change_language('es'))
language_menu.addAction(spanish_action)
```

---

## פתרון בעיות

### בעיה: השפה לא משתנה

**פתרון:**
```
1. ודא שסגרת את התוכנה לחלוטין
2. בדוק בקובץ config.yaml שהשפה נשמרה
3. הפעל מחדש מהטרמינל כדי לראות שגיאות
```

### בעיה: חלק מהטקסט לא מתורגם

**פתרון:**
```
זה תקין. לא כל הטקסטים תורגמו (כגון שגיאות טכניות).
השגיאות הטכניות נשארות באנגלית לצורך דיבוג.
```

### בעיה: תווים מוזרים בעברית

**פתרון:**
```powershell
# הפעל PowerShell כמנהל:
[console]::OutputEncoding = [System.Text.Encoding]::UTF8
# הפעל מחדש את התוכנה
```

---

## מאפיינים מתקדמים

### תרגום דינמי
התוכנה תומכת בתרגום דינמי עם פרמטרים:

```python
# דוגמה:
self.i18n.t('messages.extraction_complete', count=5)

# יוצא:
# עברית: "חולצו 5 מחיצות"
# English: "Extracted 5 partitions"
# Français: "5 partitions extraites"
```

### תרגום מקונן
יש תמיכה במפתחות מקוננים:

```python
self.i18n.t('device_panel.status.connected')
# עברית: "מחובר"
# English: "Connected"
# Français: "Connecté"
```

---

## קבצי תרגום

מיקום הקבצים:
```
translations/
├── en.yaml  # English (150+ מחרוזות)
├── he.yaml  # עברית (150+ מחרוזות)
└── fr.yaml  # Français (150+ מחרוזות)
```

כל קובץ מכיל:
- 🔤 **כותרות חלונות**
- 📋 **תפריטים**
- 🔘 **כפתורים**
- 📊 **פאנלים**
- 💬 **הודעות**
- ⚠️ **שגיאות**
- 📂 **Workspace**

---

## טיפים למתרגמים

### שמור על עקביות
```yaml
# טוב:
connect: "התחבר"
disconnect: "התנתק"

# פחות טוב:
connect: "התחבר"
disconnect: "נתק" # חסר ה' הידיעה
```

### השתמש בתווים מיוחדים
```yaml
# עבור שורות חדשות:
message: |
  שורה ראשונה
  שורה שנייה

# עבור תבניות:
greeting: "שלום, {name}!"
```

### בדוק אורכי טקסט
```yaml
# באנגלית:
button: "OK"

# בצרפתית (יותר ארוך):
button: "D'accord"

# ודא שהכפתורים מספיק רחבים!
```

---

## סיכום

✅ **3 שפות מלאות**
✅ **התאמה אוטומטית של כיוון (RTL/LTR)**
✅ **תרגום כל ממשק המשתמש**
✅ **זיהוי מכשירים מתקדם בכל השפות**
✅ **תמיכה ב-Bricked/Off devices**

**נהנה מהתוכנה במספר שפות! 🌍**
