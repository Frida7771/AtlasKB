import uuid
import math
from datetime import datetime
from typing import Optional, List, Dict, Any

from dao.kb_dao import (
    create_kb,
    update_kb,
    delete_kb,
    list_kb,
    get_kb,
    create_doc,
    update_doc,
    delete_doc,
    list_docs,
    get_doc,
    upsert_doc_embeddings,
    list_doc_embeddings,
)
from models.kb import (
    KnowledgeBase,
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeDocument,
    KnowledgeDocumentCreate,
    KnowledgeDocumentUpdate,
    KnowledgeQAReply,
)
from service.openai_service import chat_completion, create_embeddings


def _now_ms() -> int:
    return int(datetime.utcnow().timestamp() * 1000)


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ==== 知识库 ====


def create_kb_service(req: KnowledgeBaseCreate) -> KnowledgeBase:
    kb = KnowledgeBase(
        uuid=str(uuid.uuid4()),
        name=req.name,
        description=req.description,
        create_at=_now_ms(),
        update_at=_now_ms(),
    )
    create_kb(kb.dict())
    return kb


def update_kb_service(uuid_: str, req: KnowledgeBaseUpdate) -> Optional[KnowledgeBase]:
    kb_data = get_kb(uuid_)
    if not kb_data:
        return None

    fields: Dict[str, Any] = {}
    if req.name is not None:
        fields["name"] = req.name
    if req.description is not None:
        fields["description"] = req.description
    if not fields:
        return KnowledgeBase(**kb_data)

    fields["update_at"] = _now_ms()
    update_kb(uuid_, fields)
    kb_data.update(fields)
    return KnowledgeBase(**kb_data)


def delete_kb_service(uuid_: str) -> bool:
    kb_data = get_kb(uuid_)
    if not kb_data:
        return False
    delete_kb(uuid_)
    return True


def list_kb_service(page: int, size: int) -> Dict[str, Any]:
    return list_kb(page, size)


# ==== 文档 ====


def create_doc_service(
    kb_uuid: str, req: KnowledgeDocumentCreate
) -> Optional[KnowledgeDocument]:
    if not get_kb(kb_uuid):
        return None

    doc = KnowledgeDocument(
        uuid=str(uuid.uuid4()),
        kb_uuid=kb_uuid,
        title=req.title,
        content=req.content,
        create_at=_now_ms(),
        update_at=_now_ms(),
    )
    create_doc(doc.dict())

    # 生成嵌入并写入
    _generate_and_store_embeddings_for_doc(doc)

    return doc


def update_doc_service(
    uuid_: str, req: KnowledgeDocumentUpdate
) -> Optional[KnowledgeDocument]:
    doc_data = get_doc(uuid_)
    if not doc_data:
        return None

    fields: Dict[str, Any] = {}
    if req.title is not None:
        fields["title"] = req.title
    if req.content is not None:
        fields["content"] = req.content
    if not fields:
        return KnowledgeDocument(**doc_data)

    fields["update_at"] = _now_ms()
    update_doc(uuid_, fields)
    doc_data.update(fields)
    doc = KnowledgeDocument(**doc_data)

    # 如果内容有变动，重新生成嵌入
    if req.content is not None:
        _generate_and_store_embeddings_for_doc(doc)

    return doc


def delete_doc_service(uuid_: str) -> bool:
    doc_data = get_doc(uuid_)
    if not doc_data:
        return False
    delete_doc(uuid_)
    return True


def list_docs_service(kb_uuid: str, page: int, size: int) -> Dict[str, Any]:
    return list_docs(kb_uuid, page, size)


def _chunk_text(content: str, max_chars: int = 400) -> List[str]:
    """
    目前知识库主要用于 ES 检索，不再喂给 OpenAI。
    这里保留一个简单的切分函数，方便未来按需扩展。
    """
    content = content.strip()
    if not content:
        return []
    chunks: List[str] = []
    start = 0
    while start < len(content):
        end = min(start + max_chars, len(content))
        chunks.append(content[start:end])
        start = end
    return chunks


def qa_service(kb_uuid: str, question: str, top_k: int = 3) -> Optional[KnowledgeQAReply]:
    if not get_kb(kb_uuid):
        return None

    # 不再使用知识库内容喂给 OpenAI，只做普通问答
    messages = [
        {
            "role": "user",
            "content": question,
        }
    ]
    answer = chat_completion(messages)

    # 把本次 Q&A 记入知识库，并为回答生成向量
    save_qa_to_kb(kb_uuid, question, answer)

    # context 为空，表示没有把知识库内容喂给模型
    return KnowledgeQAReply(answer=answer, context=[])


def save_qa_to_kb(kb_uuid: str, question: str, answer: str) -> None:
    """
    将一轮 Q&A 写入知识库，并为回答生成 embedding 存入向量索引。
    """
    doc = KnowledgeDocument(
        uuid=str(uuid.uuid4()),
        kb_uuid=kb_uuid,
        title=question[:50],
        content=f"Q: {question}\n\nA: {answer}",
        create_at=_now_ms(),
        update_at=_now_ms(),
    )
    create_doc(doc.dict())

    # 只为回答文本生成 embedding
    embedding = create_embeddings(answer)
    upsert_doc_embeddings(
        kb_uuid,
        doc.uuid,
        [
            {
                "uuid": str(uuid.uuid4()),
                "chunk": answer,
                "embedding": embedding,
                "create_at": _now_ms(),
            }
        ],
    )


def semantic_search_service(kb_uuid: str, query: str, top_k: int = 5) -> Optional[List[Dict[str, Any]]]:
    """
    对指定知识库做向量语义检索：
    - 为 query 生成 embedding
    - 从 kb_doc_embed_index 拉取该库下所有向量
    - 计算余弦相似度，返回 top_k 的 chunk + score
    """
    if not get_kb(kb_uuid):
        return None

    q_emb = create_embeddings(query)
    vectors = list_doc_embeddings(kb_uuid)
    scored: List[Dict[str, Any]] = []
    for item in vectors:
        emb = item.get("embedding") or []
        score = _cosine_similarity(q_emb, emb)
        scored.append(
            {
                "kb_uuid": item.get("kb_uuid"),
                "doc_uuid": item.get("doc_uuid"),
                "chunk": item.get("chunk", ""),
                "score": score,
            }
        )
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


