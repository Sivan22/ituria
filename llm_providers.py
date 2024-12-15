from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from typing import Optional, Dict, List, Any
import os
import requests
import json
from dotenv import load_dotenv
from dataclasses import dataclass
import ollama


load_dotenv()


@dataclass
class GeminiResponse:
    content: str


class GeminiProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        
    def chat(self, messages: List[Dict[str, Any]]) -> GeminiResponse:
        # Convert messages to Gemini format
        gemini_messages = []
        for msg in messages:
            # Handle both dict and LangChain message objects
            if isinstance(msg, BaseMessage):
                role = "user" if isinstance(msg, HumanMessage) else "model"
                content = msg.content
            else:
                role = "user" if msg["role"] == "human" else "model"
                content = msg["content"]
                
            gemini_messages.append({
                "role": role,
                "parts": [{"text": content}]
            })
        
        # Prepare the request
        headers = {
            "Content-Type": "application/json"
        }
        
        params = {
            "key": self.api_key
        }
        
        data = {
            "contents": gemini_messages,
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.8,
                "topK": 40,
                "maxOutputTokens": 2048,
            }
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                params=params,
                json=data,
                verify='C:\\ProgramData\\NetFree\\CA\\netfree-ca-bundle-curl.crt'
            )
            response.raise_for_status()
            
            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                return GeminiResponse(content=result["candidates"][0]["content"]["parts"][0]["text"])
            else:
                raise Exception("No response generated")
                
        except Exception as e:
            raise Exception(f"Error calling Gemini API: {str(e)}")

    def invoke(self, messages: List[BaseMessage], **kwargs) -> GeminiResponse:
        return self.chat(messages)

    def generate(self, prompts, **kwargs) -> GeminiResponse:
        if isinstance(prompts, str):
            return self.invoke([HumanMessage(content=prompts)])
        elif isinstance(prompts, list):
            return self.invoke([HumanMessage(content=prompts[0])])
        raise ValueError("Unsupported prompt format")

class LLMProvider:
    def __init__(self):
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
        if google_key := os.getenv('GOOGLE_API_KEY'):
            self.providers['Gemini'] = GeminiProvider(api_key=google_key)
        
        # Anthropic
        if anthropic_key := os.getenv('ANTHROPIC_API_KEY'):
            self.providers['Claude'] = ChatAnthropic(
                api_key=anthropic_key,
                model_name="claude-3-5-sonnet-20241022",
            )

        # OpenAI
        if openai_key := os.getenv('OPENAI_API_KEY'):
            self.providers['ChatGPT'] = ChatOpenAI(
                api_key=openai_key,
                model_name="gpt-4o-2024-11-20"
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
