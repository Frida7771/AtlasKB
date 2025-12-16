from typing import Optional, List

from pydantic import BaseModel


class Chat(BaseModel):
    """对话会话"""

    uuid: str
    kb_uuid: Optional[str] = None  # 绑定的知识库，可空（纯 LLM 聊天）
    title: str
    user_uuid: str  # 发起人
    create_at: int
    update_at: int


class ChatCreate(BaseModel):
    """创建对话"""

    kb_uuid: Optional[str] = None
    title: Optional[str] = None
    first_question: Optional[str] = None


class ChatMessage(BaseModel):
    """单条消息"""

    uuid: str
    chat_uuid: str
    role: str  # user / assistant / system
    content: str
    create_at: int


class ChatMessageCreate(BaseModel):
    """用户发送消息"""

    content: str


class ChatReply(BaseModel):
    """模型回复 + 上下文"""

    answer: str
    context: List[str]


CHAT_INDEX = "chat_index"
CHAT_MESSAGE_INDEX = "chat_message_index"


