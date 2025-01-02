import streamlit as st
import os
from typing import Optional, List
from dotenv import load_dotenv
import gdown
import llm_providers
import tantivy_search
import agent
import json
import zipfile


INDEX_PATH = "./index"

# Load environment variables
load_dotenv()

class SearchAgentUI:
    index_path = INDEX_PATH
    gdrive_index_id = os.getenv("GDRIVE_INDEX_ID", "1lpbBCPimwcNfC0VZOlQueA4SHNGIp5_t")

   
    @st.cache_resource
    def get_agent(_self): 
        index_path = INDEX_PATH
        return agent.Agent(index_path)    

    def download_index_from_gdrive(self) -> bool:
        try:
            zip_path = "index.zip"
            url = f"https://drive.google.com/uc?id={self.gdrive_index_id}"
            gdown.download(url, zip_path, quiet=False)  
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(".")
            os.remove(zip_path) 
            return True
        
        except Exception as e:
            st.error(f"Failed to download index: {str(e)}")
            return False
        
        
    @st.cache_resource
    def initialize_system(_self,api_keys:dict[str,str]) -> tuple[bool, str, List[str]]:
        
        try:
            # download index
            if not os.path.exists(_self.index_path):
                st.warning("Index folder not found. Attempting to download from Google Drive...")
                if not _self.download_index_from_gdrive():
                    return False, "שגיאה: לא ניתן להוריד את האינדקס", []
                st.success("Index downloaded successfully!")
            _self.llm_providers = llm_providers.LLMProvider(api_keys)   
            available_providers = _self.llm_providers.get_available_providers()
            if not available_providers:
                return False, "שגיאה: לא נמצאו ספקי AI זמינים. אנא הזן מפתח API אחד לפחות.", []           
            return True, "המערכת מוכנה לחי শবפש", available_providers
         
        except Exception as ex:
            return False, f"שגיאה באתחול המערכת: {str(ex)}", []

    def update_messages(self, messages):
        st.session_state.messages = messages
        
    def main(self):
        st.set_page_config(
            page_title="איתוריא",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        
        # Enhanced styling with better visual hierarchy and modern design
        st.markdown("""
        <style>
            /* Global RTL Support */
            .stApp {
                direction: rtl;
                background-color: #f8f9fa;
            }
            
            /* Input Fields RTL */
            .stTextInput > div > div > input,
            .stSelectbox > div > div > div,
            .stNumberInput > div > div > input {
                direction: rtl;
                border-radius: 8px !important;
                border: 2px solid #e2e8f0 !important;
                padding: 0.75rem !important;
                transition: all 0.3s ease;
            }
            
            .stTextInput > div > div > input:focus,
            .stSelectbox > div > div > div:focus {
                border-color: #4299e1 !important;
                box-shadow: 0 0 0 1px #4299e1 !important;
            }
            
            /* Message Containers */
            .chat-container {
                background: white;
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            /* Tool Calls Styling */
            .tool-call {
                background: #f0f7ff;
                border-radius: 8px;
                padding: 1rem;
                margin: 0.5rem 0;
                border-right: 4px solid #3182ce;
            }
            
            /* Search Results */
            .search-step {
                background: white;
                border-radius: 10px;
                padding: 1.25rem;
                margin: 1rem 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                border: 1px solid #e2e8f0;
            }
            
            .document-group {
                background: #f7fafc;
                border-radius: 8px;
                padding: 1rem;
                margin: 0.75rem 0;
                border: 1px solid #e2e8f0;
            }
            
            .document-item {
                background: white;
                border-radius: 6px;
                padding: 1rem;
                margin: 0.5rem 0;
                border: 1px solid #edf2f7;
            }
            
            /* Sidebar Styling */
            [data-testid="stSidebar"] {
                direction: rtl;
                background-color: #f8fafc;
                padding: 2rem 1rem;
            }
            
            .sidebar-content {
                padding: 1rem;
            }
            
            /* Chat Messages */
            .stChatMessage {
                direction: rtl;
                background: white !important;
                border-radius: 12px !important;
                padding: 1rem !important;
                margin: 0.75rem 0 !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
            }
            
            /* Buttons */
            .stButton > button {
                border-radius: 8px !important;
                padding: 0.5rem 1.5rem !important;
                background-color: #3182ce !important;
                color: white !important;
                border: none !important;
                transition: all 0.3s ease !important;
            }
            
            .stButton > button:hover {
                background-color: #2c5282 !important;
                transform: translateY(-1px);
            }
            
            /* Code Blocks */
            .stCodeBlock {
                direction: ltr;
                text-align: left;
                border-radius: 8px !important;
                background: #2d3748 !important;
            }
            
            /* Links */
            a {
                color: #3182ce;
                text-decoration: none;
                transition: color 0.2s ease;
            }
            
            a:hover {
                color: #2c5282;
                text-decoration: underline;
            }
            
            /* Error Messages */
            .stAlert {
                border-radius: 8px !important;
                border: none !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Initialize session state for message deduplication
        if "messages" not in st.session_state:
            st.session_state.messages = []

        st.session_state.api_keys = {
            'google': "",
            'openai': "",
            'anthropic': ""
        }

        # Sidebar settings
        with st.sidebar:
            st.title("הגדרות")
            
            st.subheader("הגדרת מפתחות API")
            
            # API Key inputs with improved styling
            for provider, label in [
                ('google', 'Google API Key'),
                ('openai', 'OpenAI API Key'),
                ('anthropic', 'Anthropic API Key')
            ]:
                key = st.text_input(
                    label,
                    value=st.session_state.api_keys[provider],
                    type="password",
                    key=f"{provider}_key",
                    help=f"הזן את מפתח ה-API של {label}"
                )
                st.session_state.api_keys[provider] = key
                
                # Provider-specific links
                links = {
                    'google': 'https://aistudio.google.com/app/apikey',
                    'openai': 'https://platform.openai.com/account/api-keys',
                    'anthropic': 'https://console.anthropic.com/'
                }
                st.html(f'<small> ניתן להשיג מפתח <a href="{links[provider]}">כאן</a> </small>')

            st.markdown("---")

        # Initialize system
        success, status_msg, available_providers = self.initialize_system(st.session_state.api_keys)

        if not success:
            st.error(status_msg)
            return
        
        agent = self.get_agent()

        # Provider selection in sidebar
        with st.sidebar:
          
                if 'provider' not in st.session_state or st.session_state.provider not in available_providers:
                    st.session_state.provider = available_providers[0] 
                
                provider = st.selectbox(
                    "ספק בינה מלאכותית",
                    options=available_providers,
                    key='provider',
                    help="בחר את מודל הAI לשימוש (רק מודלים עם מפתח API זמין יוצגו)"
                )
                if agent:
                    agent.set_llm(provider)



        # Main chat interface
        
        query = st.chat_input("הזן שאלה", key="chat_input")        
        if query:
           stream = agent.chat(query)
           for chunk in stream:
                st.session_state.messages = chunk["messages"]
        if st.button("צ'אט חדש"):
            st.session_state.messages = []
            agent.clear_chat()
           
        for message in st.session_state.messages: 
                if message.type == "tool":                            
                                    if message.name == "search":
                                        results =json.loads(message.content) if message.content else []
                                        with st.expander(f"🔍 תוצאות חיפוש: {len(results)}"):
                                            for result in results:
                                                st.write(result['reference'])
                                                st.info(result['text'])
                                    elif message.name == "get_text":
                                        st.expander(f"📝 טקסט: {message.content}")
                                    
                elif message.type == "ai" :
                    if message.content != "":
                      
                        with st.chat_message(message.type):
                            if isinstance(message.content, list):
                                for item in message.content:
                                    if ('text' in item):
                                        st.write(item['text'])                                

                            else:
                                st.write(message.content)
                                
                    for tool_call in message.tool_calls:
                        with st.expander(f"🛠️ שימוש בכלי: {tool_call["name"]}"):
                            st.json(tool_call["args"])                                
                else: 
                    with st.chat_message(message.type):
                        st.write(message.content)  
           

if __name__ == "__main__":
    app = SearchAgentUI()
    app.main()
