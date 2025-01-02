import json
from random import choices
import string
from langchain.tools import BaseTool
import requests
from dotenv import load_dotenv
from dataclasses import dataclass
from langchain_core.language_models.chat_models import BaseChatModel
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
    cast,
)
from langchain_core.callbacks import (
    CallbackManagerForLLMRun,
)
from langchain_core.callbacks.manager import AsyncCallbackManagerForLLMRun
from langchain_core.exceptions import OutputParserException
from langchain_core.language_models import LanguageModelInput
from langchain_core.language_models.chat_models import BaseChatModel, LangSmithParams
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
    SystemMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool


class ChatGemini(BaseChatModel): 
     
    @property
    def _llm_type(self) -> str:
        """Get the type of language model used by this chat model."""
        return "gemini"

    api_key :str
    base_url:str =  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
    model_kwargs: Any = {}
    
    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,     
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a chat response using the Gemini API.
        
        This method handles both regular text responses and function calls.
        For function calls, it returns a ToolMessage with structured function call data
        that can be processed by Langchain's agent executor.
        
        Function calls are returned with:
        - tool_name: The name of the function to call
        - tool_call_id: A unique identifier for the function call (name is used as Gemini doesn't provide one)
        - content: The function arguments as a JSON string
        - additional_kwargs: Contains the full function call details
        
        Args:
            messages: List of input messages
            stop: Optional list of stop sequences
            run_manager: Optional callback manager
            **kwargs: Additional arguments passed to the Gemini API
            
        Returns:
            ChatResult containing either an AIMessage for text responses
            or a ToolMessage for function calls
        """
        # Convert messages to Gemini format
        gemini_messages = []
        system_message = None
        for msg in messages:
            # Handle both dict and LangChain message objects
            if isinstance(msg, BaseMessage):
                if isinstance(msg, SystemMessage):
                    system_message = msg.content
                    kwargs["system_instruction"]= {"parts":[{"text": system_message}]}
                    continue
                if isinstance(msg, HumanMessage):
                    role = "user"
                    content = msg.content
                elif isinstance(msg, AIMessage):
                    role = "model"
                    content = msg.content
                elif isinstance(msg, ToolMessage):
                    # Handle tool messages by adding them as function outputs
                    gemini_messages.append(
                        {
                        "role": "model",
                        "parts": [{
                        "functionResponse": {
                            "name": msg.name,
                            "response": {"name": msg.name, "content": msg.content},                         
                        }}]}
                   )
                    continue
            else:
                role = "user" if msg["role"] == "human" else "model"
                content = msg["content"]
                
            message_part = {
                "role": role,
                "parts":[{"functionCall": { "name": msg.tool_calls[0]["name"], "args": msg.tool_calls[0]["args"]}}] if isinstance(msg, AIMessage) and msg.tool_calls else [{"text": content}]
            }
            gemini_messages.append(message_part)
            
       
        
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
            },
            **kwargs
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
            if "candidates" in result and len(result["candidates"]) > 0 and "parts" in result["candidates"][0]["content"]:
                parts = result["candidates"][0]["content"]["parts"]
                tool_calls = []
                content = ""
                for part in  parts: 
                    if "text" in part:
                        content += part["text"]                                      
                    if "functionCall" in part:                       
                        function_call = part["functionCall"]
                        tool_calls.append( {
                                    "name": function_call["name"],
                                    "id": function_call["name"]+random_string(5), # Gemini doesn't provide a unique id,}
                                    "args": function_call["args"],
                                    "type": "tool_call",})  
                    # Create a proper ToolMessage with structured function call data
                return ChatResult(generations=[
                        ChatGeneration(
                            message=AIMessage(
                                content=content,
                                tool_calls=tool_calls,                                
                            ) if len(tool_calls) > 0 else AIMessage(content=content)
                        )
                    ])
                
        
            else:
                raise Exception("No response generated")
                
        except Exception as e:
            raise Exception(f"Error calling Gemini API: {str(e)}")

   
    def bind_tools(
        self,
        tools: Sequence[Union[Dict[str, Any], Type, Callable, BaseTool]],
        *,
        tool_choice: Optional[Union[dict, str, Literal["auto", "any"], bool]] = None,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, BaseMessage]:
        """Bind tool-like objects to this chat model.


        Args:
            tools: A list of tool definitions to bind to this chat model.
                Supports any tool definition handled by
                :meth:`langchain_core.utils.function_calling.convert_to_openai_tool`.
            tool_choice: If provided, which tool for model to call. **This parameter
                is currently ignored as it is not supported by Ollama.**
            kwargs: Any additional parameters are passed directly to
                ``self.bind(**kwargs)``.
        """
        
        formatted_tools = {"function_declarations": [convert_to_gemini_tool(tool) for tool in tools]}
        return super().bind(tools=formatted_tools, **kwargs)
    
def convert_to_gemini_tool(
    tool: Union[BaseTool],
    *,
    strict: Optional[bool] = None,
) -> dict[str, Any]:
    """Convert a tool-like object to an Gemini tool schema.

    Gemini tool schema reference:
   https://ai.google.dev/gemini-api/docs/function-calling#function_calling_mode

    Args:
        tool:           
            BaseTool. 
        strict:
            If True, model output is guaranteed to exactly match the JSON Schema
            provided in the function definition. If None, ``strict`` argument will not
            be included in tool definition.

    Returns:
        A dict version of the passed in tool which is compatible with the
        Gemini tool-calling API.
    """
    if isinstance(tool, BaseTool):
        # Extract the tool's schema
        schema = tool.args_schema.schema() if tool.args_schema else {"type": "object", "properties": {}}
        
        #convert to gemini schema 
        raw_properties = schema.get("properties", {})
        properties = {}
        for key, value in raw_properties.items():
            properties[key] = {
                "type": value.get("type", "string"),
                "description": value.get("title", ""),
            }
        
        
        # Build the function definition
        function_def = {
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": schema.get("required", [])
            }
        }
        
        if strict is not None:
            function_def["strict"] = strict
            
        return function_def
    else:
        raise ValueError(f"Unsupported tool type: {type(tool)}")

def random_string(length: int) -> str:
    return ''.join(choices(string.ascii_letters + string.digits, k=length))
    