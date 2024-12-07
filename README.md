<<<<<<< HEAD
# Ituria - AI-Powered Intelligent Search System

![alt text](image.png)

## Overview
This project implements an intelligent search system that utilizes a multi-stage language model approach: First, the model generates the search query, then the system searches using the search engine, the results are sent back to the model for ranking, and if necessary, a request for an additional query and search is made. At the end of the process, the language model summarizes the search results and attempts to answer the original question.

## Features
- Smart document indexing with Tantivy for improved search relevance
- Flexible LLM provider support (Claude, GPT, Ollama)
- Intelligent keyword extraction from natural language questions
- Automatic evaluation and improvement of search results
- Multi-attempt search strategy with confidence scoring
- Context-aware answer generation
- Comprehensive error handling and logging
- Support for multilingual queries and documents
- Customizable search parameters (max iterations, results per search)

## Prerequisites
- Python 3.11 or higher
- Tantivy index from Otzaria application
- At least one of the following API keys (stored in `.env`):
  - Anthropic API key (for Claude)
  - OpenAI API key (for GPT)
  - Google API key (for Gemini)
  - Local Ollama setup (for open-source models)
=======
# סוכן חיפוש מסמכים מבוסס בינה מלאכותית

![alt text](image.png)

## סקירה כללית
פרויקט זה מיישם מערכת חיפוש ושאלות-תשובות חכמה המשלבת:
- Tantivy לאינדוקס ואחזור מסמכים יעיל
- Claude-3 של Anthropic לחילוץ מילות מפתח, הערכת תוצאות ויצירת תשובות
- תהליך עבודה מותאם אישית לשיפור דיוק התשובות

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
>>>>>>> origin/main

## התקנה
1. שכפל את המאגר
2. התקן את התלויות:
```bash
pip install -r requirements.txt
```

<<<<<<< HEAD
3. Set up a `.env` file with your credentials:
```
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
```

## Usage
### Quick Start
Run the Flet UI to see the system in action:

=======
3. הגדר קובץ `.env` עם האישורים שלך:
```
ANTHROPIC_API_KEY=your_anthropic_api_key
```

## שימוש
### התחלה מהירה
הפעל את ממשק המשתמש של Flet כדי לראות את המערכת בפעולה:

>>>>>>> origin/main
```bash
python flet_ui.py
```

<<<<<<< HEAD
The user interface allows you to:
- Select a Tantivy index directory
- Choose your preferred LLM provider (Claude, GPT, Gemini or Ollama)
- Set maximum search iterations
- Define number of results per search
- View detailed search process steps
- See highlighted search results

## How It Works
The system employs a sophisticated multi-stage approach:

1. **Query Generation**: The selected LLM analyzes the user's question and generates effective search queries
2. **Document Search**: Utilizes Tantivy for high-performance document indexing and retrieval
3. **Result Evaluation**: The LLM evaluates search results and determines if additional searches are needed
4. **Answer Generation**: Synthesizes information from search results to provide comprehensive answers

## Dependencies
Key dependencies include:
- `langchain` and related packages for LLM integration
- `flet` for the user interface
- `tantivy` for document indexing and search
- `python-dotenv` for environment management
- Various LLM provider packages (anthropic, openai, ollama)

## Configuration
- Modify `tantivy_search_agent.py` to customize search settings
- Adjust `agent_workflow.py` to configure:
  - Confidence thresholds
  - LLM parameters
  - Search iteration logic
- Update `llm_providers.py` to add or modify LLM providers
- Customize `flet_ui.py` for UI modifications

## Security
- Store API keys and sensitive data in environment variables
- Never upload your `.env` file to version control
- Ensure proper access controls for the Tantivy index

## Troubleshooting
- Verify the Tantivy index exists and is accessible
- Check API key permissions for your chosen LLM provider
- Ensure proper file permissions for the document library
- Review logs for detailed error information

## Contributing
Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.
=======
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
>>>>>>> origin/main

## תרומה
תרומות מתקבלות בברכה! אנא שלח בקשות משיכה או פתח סוגיות עבור באגים ובקשות תכונות.

## רישיון
MIT
