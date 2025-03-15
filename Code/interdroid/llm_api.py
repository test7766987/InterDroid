from abc import ABC, abstractmethod
import requests
from typing import List, Dict, Any, Optional, Union
import base64
from pathlib import Path
import re
import dashscope
from openai import OpenAI

class BaseLLMAPI(ABC):
    """Base class for LLM API"""
    
    @abstractmethod
    def chat_completion(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        pass

    @staticmethod
    def encode_image_to_base64(image_path: Union[str, Path]) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    @staticmethod
    def is_base64(s: str) -> bool:
        try:
            return base64.b64encode(base64.b64decode(s)).decode('utf-8') == s
        except Exception:
            return False

    @staticmethod
    def is_url(s: str) -> bool:
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(url_pattern.match(s))

class SiliconFlowAPI(BaseLLMAPI):
    """Silicon Flow API Implementation"""
    
    def __init__(self, api_key: str, model: str = "deepseek-ai/DeepSeek-V3"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.siliconflow.cn/v1/chat/completions"
        
    def process_image(self, image: Union[str, Path]) -> Dict[str, Any]:
        if isinstance(image, str):
            if self.is_url(image):
                return {
                    "type": "image_url",
                    "image_url": {"url": image}
                }
            elif self.is_base64(image):
                return {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image}"}
                }
            else:
                image_base64 = self.encode_image_to_base64(image)
                return {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                }
        else:
            image_base64 = self.encode_image_to_base64(image)
            return {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
            }

    def format_message(self, role: str, content: Union[str, List[Union[str, Dict, Path]]], **kwargs) -> Dict[str, Any]:
        if isinstance(content, str):
            return {"role": role, "content": content}
        
        formatted_content = []
        for item in content:
            if isinstance(item, str):
                if any(item.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                    formatted_content.append(self.process_image(item))
                else:
                    formatted_content.append({
                        "type": "text",
                        "text": item
                    })
            elif isinstance(item, Path) and any(str(item).lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                formatted_content.append(self.process_image(item))
            elif isinstance(item, dict):
                formatted_content.append(item)
                
        return {"role": role, "content": formatted_content}

    def chat_completion(
        self, 
        messages: List[Union[Dict[str, Any], tuple]],
        stream: bool = False,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        top_p: float = 0.7,
        top_k: int = 50,
        frequency_penalty: float = 0.5,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        
        formatted_messages = []
        for message in messages:
            if isinstance(message, dict):
                formatted_messages.append(message)
            elif isinstance(message, tuple):
                role, content = message
                formatted_messages.append(self.format_message(role, content))
                
        import json
        with open('msg.json', 'w', encoding='utf-8') as f:
            json.dump(formatted_messages, f, ensure_ascii=False, indent=2)

        
        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "stream": stream,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "frequency_penalty": frequency_penalty,
            "stop": stop or ["null"],
            "n": 1,
            "response_format": {"type": "text"}
        }
        
        if kwargs.get("tools"):
            payload["tools"] = kwargs["tools"]
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(self.base_url, json=payload, headers=headers)

        return response.json()

class DashScopeAPI(BaseLLMAPI):
    """DashScope API Implementation"""
    
    def __init__(self, api_key: str, model: str = "qwen2.5-vl-72b-instruct"):
        dashscope.api_key = api_key
        self.model = model
        self._client = dashscope
        
    def process_image(self, image: Union[str, Path]) -> Dict[str, Any]:
        if isinstance(image, str):
            if self.is_url(image):
                return {"image": image}
            elif self.is_base64(image):
                return {"image": f"data:image/jpeg;base64,{image}"}
            else:
                image_base64 = self.encode_image_to_base64(image)
                return {"image": f"data:image/jpeg;base64,{image_base64}"}
        else:
            image_base64 = self.encode_image_to_base64(image)
            return {"image": f"data:image/jpeg;base64,{image_base64}"}

    def format_message(self, role: str, content: Union[str, List[Union[str, Dict, Path]]], **kwargs) -> Dict[str, Any]:
        if isinstance(content, str):
            return {"role": role, "content": [{"text": content}]}
        
        formatted_content = []
        for item in content:
            if isinstance(item, str):
                if any(item.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                    formatted_content.append(self.process_image(item))
                else:
                    formatted_content.append({"text": item})
            elif isinstance(item, Path) and any(str(item).lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                formatted_content.append(self.process_image(item))
            elif isinstance(item, dict):
                formatted_content.append(item)
                
        return {"role": role, "content": formatted_content}

    def chat_completion(
        self, 
        messages: List[Union[Dict[str, Any], tuple]],
        stream: bool = False,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        frequency_penalty: float = 1.0,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        
        formatted_messages = []
        for message in messages:
            if isinstance(message, dict):
                formatted_messages.append(message)
            elif isinstance(message, tuple):
                role, content = message
                formatted_messages.append(self.format_message(role, content))

        response = self._client.MultiModalConversation.call(
            model=self.model,
            messages=formatted_messages,
            stream=stream,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repetition_penalty=frequency_penalty,
            stop=stop,
        )
        
        return response

class OpenAIAPI(BaseLLMAPI):
    """OpenAI API Implementation"""
    
    def __init__(self, api_key: str, model: str = "gpt-4-vision-preview", base_url: Optional[str] = None):
        """
        Initialize OpenAI API client
        
        Args:
            api_key: OpenAI API key
            model: Model name, default is gpt-4-vision-preview
            base_url: Base API URL for custom endpoints
        """
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        
    def process_image(self, image: Union[str, Path]) -> Dict[str, Any]:
        if isinstance(image, str):
            if self.is_url(image):
                return {
                    "type": "image_url",
                    "image_url": image
                }
            elif self.is_base64(image):
                return {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{image}"
                }
            else:
                image_base64 = self.encode_image_to_base64(image)
                return {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{image_base64}"
                }
        else:
            image_base64 = self.encode_image_to_base64(image)
            return {
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{image_base64}"
            }

    def format_message(self, role: str, content: Union[str, List[Union[str, Dict, Path]]], **kwargs) -> Dict[str, Any]:
        if isinstance(content, str):
            return {"role": role, "content": content}
        
        formatted_content = []
        for item in content:
            if isinstance(item, str):
                if any(item.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                    formatted_content.append(self.process_image(item))
                else:
                    formatted_content.append({
                        "type": "text",
                        "text": item
                    })
            elif isinstance(item, Path) and any(str(item).lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                formatted_content.append(self.process_image(item))
            elif isinstance(item, dict):
                formatted_content.append(item)
                
        return {"role": role, "content": formatted_content}

    def chat_completion(
        self, 
        messages: List[Union[Dict[str, Any], tuple]],
        stream: bool = False,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        top_p: float = 0.7,
        frequency_penalty: float = 0.5,
        presence_penalty: float = 0.0,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat request to OpenAI API
        
        Args:
            messages: List of messages
            stream: Whether to use streaming response
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature parameter
            top_p: Top-p sampling parameter
            frequency_penalty: Frequency penalty parameter
            presence_penalty: Presence penalty parameter
            stop: Stop sequences
            **kwargs: Additional parameters
        """
        formatted_messages = []
        for message in messages:
            if isinstance(message, dict):
                formatted_messages.append(message)
            elif isinstance(message, tuple):
                role, content = message
                formatted_messages.append(self.format_message(role, content))

        response = self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            stream=stream,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stop=stop,
        )
        
        if stream:
            return response
        
        return {
            "choices": [{
                "message": {
                    "role": response.choices[0].message.role,
                    "content": response.choices[0].message.content
                }
            }]
        }

# Usage examples
if __name__ == "__main__":
    # api = SiliconFlowAPI(
    #     api_key="<your-silicon-flow-api-key>",
    #     model="Pro/Qwen/Qwen2-VL-7B-Instruct"
    # )
    
    # Method 1: Using tuple format (recommended, more concise)
    # messages = [
    #     ("user", [
    #         "./image.png",  # Local image path
    #         "Please describe the content of this image"  # Text prompt
    #     ])
    # ]
    
    # Method 2: Using complete dictionary format
    # messages_dict = [
    #     {
    #         "role": "user",
    #         "content": [
    #             {
    #                 "type": "image_url",
    #                 "image_url": {
    #                     "url": f"data:image/png;base64,{api.encode_image_to_base64('./image.png')}"
    #                 }
    #             },
    #             {
    #                 "type": "text",
    #                 "text": "Please describe the content of this image"
    #             }
    #         ]
    #     }
    # ]
    
    # Send request and get response
    # response = api.chat_completion(messages)  # or use messages_dict
    # print(response)
    
    # DashScope API usage example
    dashscope_api = DashScopeAPI(
        api_key="<your-dashscope-api-key>",
        model="qwen2.5-vl-72b-instruct"
    )
    
    messages = [
        ("user", [
            "./screenshots/1.jpg",  # Local image path
            "I want to set a personal avatar, please tell me where to click, analyze and provide the grounding of the component that needs to be clicked"  # Text prompt
        ])
    ]
    
    response = dashscope_api.chat_completion(messages)
    print(response)
    
    # OpenAI API usage example
    openai_api = OpenAIAPI(
        api_key="<your-openai-api-key>",
        model="gpt-4-vision-preview"
    )
    
    messages = [
        ("user", [
            "./image.jpg",  # Local image path
            "Please describe the content of this image"  # Text prompt
        ])
    ]
    
    response = openai_api.chat_completion(messages)
    print(response)