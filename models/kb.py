from typing import Optional, List

from pydantic import BaseModel


class KnowledgeBase(BaseModel):
    """知识库实体"""

    uuid: str
    name: str
    description: Optional[str] = None
    create_at: int
    update_at: int


class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求"""

    name: str
    description: Optional[str] = None


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求"""

    name: Optional[str] = None
    description: Optional[str] = None


class KnowledgeDocument(BaseModel):
    """知识库文档"""

    uuid: str
    kb_uuid: str
    title: str
    content: str
    create_at: int
    update_at: int


class KnowledgeDocumentCreate(BaseModel):
    """创建/导入文档请求"""

    title: str
    content: str


class KnowledgeDocumentUpdate(BaseModel):
    """更新文档请求"""

    title: Optional[str] = None
    content: Optional[str] = None


class KnowledgeQARequest(BaseModel):
    """知识库问答请求"""

    question: str
    top_k: int = 3


class KnowledgeQAReply(BaseModel):
    """知识库问答响应"""

    answer: str
    context: List[str]


KB_INDEX = "kb_index"
KB_DOC_INDEX = "kb_doc_index"
KB_DOC_EMBED_INDEX = "kb_doc_embed_index"


