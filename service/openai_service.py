from openai import OpenAI
from define import OPENAI_API_KEY
from typing import Optional, List, Dict

_client: Optional[OpenAI] = None


def get_openai_client() -> OpenAI:
    """获取 OpenAI 客户端（单例模式）"""
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 未配置，请在 .env 文件中设置")
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def chat_completion(messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo") -> str:
    """
    OpenAI 聊天完成接口
    
    Args:
        messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
        model: 使用的模型，默认为 gpt-3.5-turbo
    
    Returns:
        模型返回的文本内容
    """
    client = get_openai_client()
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    return response.choices[0].message.content


def create_embeddings(text: str, model: str = "text-embedding-ada-002") -> List[float]:
    """
    创建文本嵌入向量
    
    Args:
        text: 要嵌入的文本
        model: 使用的嵌入模型，默认为 text-embedding-ada-002
    
    Returns:
        嵌入向量列表
    """
    client = get_openai_client()
    response = client.embeddings.create(
        model=model,
        input=text
    )
    return response.data[0].embedding

