from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from typing import Optional, Dict, List, Any, Sequence
from langchain.tools import BaseTool
import os
import requests
import json
from dotenv import load_dotenv
from dataclasses import dataclass
import ollama
import copy
from chat_gemini import ChatGemini


load_dotenv()



class LLMProvider:
    
    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        if api_keys:
            self.api_keys = api_keys
        self.providers: Dict[str, Any] = {}
        self._setup_providers()

    def _get_ollama_models(self) -> List[str]:
        """Get list of available Ollama models using the ollama package"""
        try:
            models = ollama.list()
            return [model.model for model in models['models']]
        except Exception:
            return []

    def _setup_providers(self):
        os.environ['REQUESTS_CA_BUNDLE'] = 'C:\\ProgramData\\NetFree\\CA\\netfree-ca-bundle-curl.crt'
        
        # Google Gemini
        if google_key := os.getenv('GOOGLE_API_KEY') or self.api_keys.get('google'): 
            self.providers['Gemini'] = ChatGemini(api_key=google_key)
        
        # Anthropicsel
        if anthropic_key := os.getenv('ANTHROPIC_API_KEY')  or self.api_keys.get('anthropic'):
            self.providers['Claude'] = ChatAnthropic(
                api_key=anthropic_key,
                model_name="claude-3-5-sonnet-20241022",
            )

        # OpenAI
        if openai_key := os.getenv('OPENAI_API_KEY') or self.api_keys.get('openai'):
            self.providers['ChatGPT'] = ChatOpenAI(
                api_key=openai_key,
                model_name="gpt-4o-2024-11-20",
                max_completion_tokens=4096,
              
            )

        # Ollama (local)
        try:
            # Get available Ollama models using the ollama package
            ollama_models = self._get_ollama_models()
            for model in ollama_models:
                self.providers[f'Ollama-{model}'] = ChatOllama(model=model)
        except Exception:
            pass  # Ollama not available

    def get_available_providers(self) -> list[str]:        
        """Return list of available provider names"""
  
        return list(self.providers.keys())

    def get_provider(self, name: str) -> Optional[Any]:
        """Get LLM provider by name"""
        return self.providers.get(name)
