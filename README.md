# איתוריא - חיפוש חכם מבוסס סוכן בינה מלאכותית

![alt text](image.png)

## סקירה כללית
פרויקט זה מיישם מערכת חיפוש חכמה שעושה שימוש רב שלבי במודל שפה: ראשית המודל יוצר את השאילתה לחיפוש, לאחר מכן המערכת מחפשת אותו במנוע חיפוש, התוצאות נשלחות למודל לדירוג, ובמקרה הצורך נשלחת בקשה ליצירת שאילתה נוספת וחיפוש נוסף, בסוף התהליך, מודל השפה מסכם את תוצאות החיפוש ומנסה לענות על השאלה המקורית.

## תכונות
- אינדוקס מסמכים חכם עם Tantivy לשיפור רלוונטיות החיפוש
- חילוץ חכם של מילות מפתח משאלות בשפה טבעית
- הערכה ושיפור אוטומטיים של תוצאות החיפוש
- אסטרטגיית חיפוש מרובת ניסיונות עם ציוני ביטחון
- יצירת תשובות מודעת הקשר באמצעות Claude-3
- טיפול מקיף בשגיאות ותיעוד
- תמיכה בשאילתות ומסמכים רב-לשוניים
- פרמטרים מותאמים אישית לחיפוש (מספר איטרציות מקסימלי, תוצאות לחיפוש)

## דרישות מוקדמות
- Python 3.11 ומעלה
- אינדקס Tantivy מאפליקציית אוצריה
- מפתח API של Anthropic (נדרשת גישה ל-Claude-3)

## התקנה
1. שכפל את המאגר
2. התקן את התלויות:
```bash
pip install -r requirements.txt
```

3. הגדר קובץ `.env` עם האישורים שלך:
```
ANTHROPIC_API_KEY=your_anthropic_api_key
```

## שימוש
### התחלה מהירה
הפעל את ממשק המשתמש של Flet כדי לראות את המערכת בפעולה:

```bash
python flet_ui.py
```

ממשק המשתמש מאפשר לך:
- לבחור תיקיית אינדקס Tantivy
- להגדיר מספר איטרציות מקסימלי לחיפוש
- לקבוע מספר תוצאות לחיפוש
- לצפות בשלבי תהליך החיפוש המפורטים
- לראות תוצאות חיפוש מודגשות

## איך זה עובד

### אינדוקס מסמכים
- המסמכים מאונדקסים מראש באמצעות Tantivy דרך אפליקציית אוצריה
- Tantivy מספק אינדוקס מסמכים יעיל ומדויק

### חיפוש ויצירת תשובות
1. **חילוץ מילות מפתח**: משתמש ב-Claude-3 לחילוץ מילות מפתח רלוונטיות מהשאלה
2. **חיפוש מסמכים**: מבצע חיפוש Tantivy עם מילות המפתח שחולצו
3. **הערכת תוצאות**: 
   - מעריך תוצאות חיפוש באמצעות Claude-3
   - מעניק ציוני ביטחון לקביעת איכות התוצאות
   - משפר אוטומטית את החיפוש אם הביטחון נמוך
4. **יצירת תשובות**: 
   - מייצר תשובות מקיפות באמצעות הקשרי מסמכים רלוונטיים
   - מבנה תשובות בצורה ברורה ומציין פערי מידע

## הגדרות
- שנה את `tantivy_search_agent.py` כדי להתאים אישית הגדרות וניתוח Tantivy
- התאם את `agent_workflow.py` כדי להגדיר:
  - ספי ביטחון
  - פרמטרים של Claude-3
  - דרישות יצירת תשובות
- התאם אישית את `flet_ui` כדי להתאים את חוויית/ממשק המשתמש לצרכיך

## אבטחה
- אחסן מפתחות API ונתונים רגישים במשתני סביבה
- לעולם אל תעלה קובץ `.env` לבקרת גרסאות
- ודא בקרות גישה נאותות לאינדקס Tantivy

## פתרון בעיות
- ודא שאינדקס Tantivy קיים ונגיש
- בדוק הרשאות מפתח API של Anthropic וגישה ל-Claude-3
- ודא הרשאות קבצים מתאימות לספריית המסמכים
- עיין ביומנים למידע מפורט על שגיאות

## תרומה
תרומות מתקבלות בברכה! אנא שלח בקשות משיכה או פתח סוגיות עבור באגים ובקשות תכונות.

## רישיון
MIT
