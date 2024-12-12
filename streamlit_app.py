import streamlit as st
from tantivy_search_agent import TantivySearchAgent
from agent_workflow import SearchAgent
import os
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SearchAgentUI:
    def __init__(self):
        self.tantivy_agent: Optional[TantivySearchAgent] = None
        self.agent: Optional[SearchAgent] = None
        self.index_path = os.getenv("INDEX_PATH", "./index")

    def get_available_providers(self) -> List[str]:
        """Get available providers without creating a SearchAgent instance"""
        temp_tantivy = TantivySearchAgent(self.index_path)
        temp_agent = SearchAgent(temp_tantivy)
        return temp_agent.get_available_providers()

    def initialize_system(self):
        try:
            self.tantivy_agent = TantivySearchAgent(self.index_path)
            if self.tantivy_agent.validate_index():
                available_providers = self.get_available_providers()
                self.agent = SearchAgent(
                    self.tantivy_agent,
                    provider_name=st.session_state.get('provider', available_providers[0])
                )
                return True, "המערכת מוכנה לחיפוש", available_providers
            else:
                return False, "שגיאה: אינדקס לא תקין", []
        except Exception as ex:
            return False, f"שגיאה באתחול המערכת: {str(ex)}", []

    def main(self):
        st.set_page_config(
            page_title="איתוריא",
            layout="wide",
            initial_sidebar_state="collapsed"
        )

        # Enhanced RTL support and styling
        st.markdown("""
        <style>
            .stApp {
                direction: rtl;
            }
            .stTextInput > div > div > input {
                direction: rtl;
            }
            .stSelectbox > div > div > div {
                direction: rtl;
            }
            .stNumberInput > div > div > input {
                direction: rtl;
            }
            .search-step {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 10px;
                margin: 5px 0;
                background-color: #f8f9fa;
            }
            .document-group {
                border: 1px solid #e3f2fd;
                border-radius: 5px;
                padding: 10px;
                margin: 5px 0;
                background-color: #f5f9ff;
            }
            .document-item {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 10px;
                margin: 5px 0;
                background-color: white;
            }
        </style>
        """, unsafe_allow_html=True)

        # Initialize system
        success, status_msg, available_providers = self.initialize_system()

        # Header layout
        col1, col2, col3 = st.columns([2,1,1])

        with col1:
            if success:
                st.success(status_msg)
            else:
                st.error(status_msg)

        with col2:
            if 'provider' not in st.session_state:
                st.session_state.provider = available_providers[0] if available_providers else None
            
            if available_providers:
                provider = st.selectbox(
                    "ספק בינה מלאכותית",
                    options=available_providers,
                    key='provider'
                )
                if self.agent:
                    self.agent.set_provider(provider)

        with col3:
            col3_1, col3_2 = st.columns(2)
            with col3_1:
                max_iterations = st.number_input(
                    "מספר נסיונות מקסימלי",
                    min_value=1,
                    value=3,
                    key='max_iterations'
                )
            with col3_2:
                results_per_search = st.number_input(
                    "תוצאות לכל חיפוש",
                    min_value=1,
                    value=5,
                    key='results_per_search'
                )

        # Search input
        query = st.text_input(
            "הכנס שאילתת חיפוש",
            disabled=not success,
            placeholder="הקלד את שאילתת החיפוש שלך כאן...",
            key='search_query'
        )

        # Search button
        if (st.button('חפש', disabled=not success) or query) and query!="" and self.agent:          
                try:
                    if 'steps' not in st.session_state:
                        st.session_state.steps = []
                    
                    steps_container = st.container()
                    answer_container = st.container()
                    sources_container = st.container()

                    with steps_container:
                        st.subheader("צעדי תהליך החיפוש")

                    def handle_step_update(step):
                        if 'final_result' in step:
                            final_result = step['final_result']
                            
                            with answer_container:
                                st.subheader("תשובה סופית")
                                st.info(final_result['answer'])

                            if final_result['sources']:
                                with sources_container:
                                    st.subheader("מסמכי מקור")
                                    st.markdown(f"נמצאו {len(final_result['sources'])} תוצאות")
                                    
                                    for i, source in enumerate(final_result['sources']):
                                        with st.expander(f"תוצאה {i+1}: {source['reference']} (ציון: {source['score']:.2f})"):
                                            st.write(source['text'])
 
                        else:
                            with steps_container:
                                step_number = len(st.session_state.steps) + 1
                                st.markdown(f"""
                                <div class='search-step'>
                                    <strong>צעד {step_number}. {step['action']}</strong>
                                </div>
                                """, unsafe_allow_html=True)
                                st.markdown(f"**{step['description']}**")
                                
                                if 'results' in step:
                                    documents = []
                                    
                                    for r in step['results']:
                                        if r['type'] == 'query':
                                            st.markdown("**שאילתת חיפוש:**")
                                            st.code(r['content'])
                                        
                                        elif r['type'] == 'document':
                                            documents.append(r['content'])
                                        
                                        elif r['type'] == 'evaluation':
                                            content = r['content']
                                            status = "✓" if content['status'] == 'accepted' else "↻"
                                            confidence = f"ביטחון: {content['confidence']}"
                                            if content['status'] == 'accepted':
                                                st.success(f"{status} {confidence}")
                                            else:
                                                st.warning(f"{status} {confidence}")
                                            if content['explanation']:
                                                st.info(content['explanation'])
                                        
                                        elif r['type'] == 'new_query':
                                            st.markdown("**ניסיון הבא:**")
                                            st.code(r['content'])
                                    
                                    # Display documents if any were found
                                    if documents:
                                        for i, doc in enumerate(documents):
                                            with st.expander(f"{doc['reference']} (ציון: {doc['score']:.2f})"):
                                                st.write(doc['highlights'][0])
                                    
                                st.markdown("---")
                            st.session_state.steps.append(step)

                    # Clear previous steps before starting new search
                    st.session_state.steps = []
                    
                    # Start the search process
                    self.agent.search_and_answer(
                        query=query,
                        num_results=results_per_search,
                        max_iterations=max_iterations,
                        on_step=handle_step_update
                    )

                except Exception as ex:
                    st.error(f"שגיאת חיפוש: {str(ex)}")

if __name__ == "__main__":
    app = SearchAgentUI()
    app.main()
