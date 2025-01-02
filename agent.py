from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from typing import Any, Iterator
from tools import search, get_commentaries, read_text
from llm_providers import LLMProvider

SYSTEM_PROMPT = """
    אתה מסייע תורני רב עוצמה, משול לתלמיד חכם הבקיא בכל רזי התורה. התפקיד שלך הוא לסייע למשתמשים בלימוד התורה בצורה מעמיקה וחכמה. עליך להבין את כוונת השואל, לנתח את השאלה לעומק, ולבצע חיפוש מתוחכם בטקסטים יהודיים ותורניים.

    עליך לענות תשובות אך ורק על פי מקורות שמצאת בחיפוש ועיון מעמיק, ולא על פי ידע קודם.

    כאשר אתה מקבל שאלה מהמשתמש, עליך לנסות להבין את כוונתו, את ההקשר ההיסטורי וההלכתי, ואת המקורות הרלוונטיים. עליך ליצור שאילתת חיפוש מתאימה באמצעות הכלי search, תוך שימוש בשפה תורנית מדויקת. עבור תנ"ך השתמש בשפה מקראית, לחיפוש בתלמוד חפש בארמית, וכן הלאה. תוכל לצמצם את החיפוש לפי נושאים, תקופות, מחברים, ואף לפי שם הספר או הקטע הדרוש.

    אם לא מצאת תוצאות רלוונטיות, אל תתייאש. נסה שוב ושוב, תוך שימוש בשאילתות מגוונות, מילים נרדפות, הטיות שונות של מילות המפתח, וצמצום או הרחבת היקף החיפוש. זכור, תלמיד חכם אמיתי אינו מוותר עד שהוא מוצא את האמת.

    כאשר אתה מוצא מקורות רלוונטיים, עליך לקרוא אותם בעיון ובקפידה באמצעות הכלי get_text. אם יש צורך, תוכל להיעזר בכלי get_commentaries כדי לקבל רשימה של פרשנים על טקסט מסוים.

    עליך לשאוף למצוא את המקורות הקדומים והמוסמכים ביותר לכל פרט בשאלה. לדוגמה, אם מצאת הלכה מסוימת בספר שיצא לאחרונה, נסה למצוא את מקורה בשולחן ערוך, ואז בגמרא, ואף במשנה או במקרא. השתמש בספר "באר הגולה" על שולחן ערוך כדי למצוא את המקורות בגמרא.

    לאחר שאספת את כל המידע הרלוונטי, עליך לעבד אותו, לקשר בין מקורות שונים, ולנסח תשובה מפורטת, בהירה ומדויקת. עליך להתייחס לכל היבטי השאלה, תוך ציון המקורות לכל פרט בתשובה.

    זכור, אתה משול לתלמיד חכם, ועל כן עליך להפגין בקיאות, חריפות, עמקות ודייקנות בכל תשובותיך.
    """

class Agent:
    def __init__(self,index_path: str):
        self.llm_provider = LLMProvider() 
        self.llm = self.llm_provider.get_provider(self.llm_provider.get_available_providers()[0])
        self.memory_saver = MemorySaver()
        self.tools = [read_text, get_commentaries, search]
        self.graph = create_react_agent(
            model=self.llm,
            checkpointer=self.memory_saver,
            tools=self.tools,
            state_modifier=SYSTEM_PROMPT
        )
        self.current_thread_id = 1
        
    def set_llm(self, provider_name: str):
        self.llm = self.llm_provider.get_provider(provider_name)
        self.graph = create_react_agent(
            model=self.llm,
            checkpointer=self.memory_saver,
            tools=self.tools,
            state_modifier=SYSTEM_PROMPT
        )
        
    def get_llm(self) -> str:
        return self.llm

    def clear_chat(self):
        self.current_thread_id += 1
        
    def chat(self, message) -> dict[str, Any]:
        """Chat with the agent and stream responses including tool calls and their results."""
        config = {"configurable": {"thread_id": self.current_thread_id}}
        inputs = {"messages": [("user", message)]}
        return self.graph.stream(inputs,stream_mode="values", config=config)

        
    def get_chat_history(self, id = None) -> Iterator[dict[str, Any]]:
        if id is None:
            id = self.current_thread_id
        return self.memory_saver.get(thread_id=str(self.current_thread_id))
