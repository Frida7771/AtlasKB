from typing import List, Dict, Any, Optional

from elasticsearch import Elasticsearch

from dao.init import get_es_client
from models.kb import KB_INDEX, KB_DOC_INDEX, KB_DOC_EMBED_INDEX


def _ensure_indices(client: Elasticsearch) -> None:
    """
    确保知识库相关索引已创建。
    使用较宽松的 mapping，适合入门场景。
    """
    # 知识库索引
    if not client.indices.exists(index=KB_INDEX):
        client.indices.create(
            index=KB_INDEX,
            mappings={
                "properties": {
                    "uuid": {"type": "keyword"},
                    "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "description": {"type": "text"},
                    "create_at": {"type": "long"},
                    "update_at": {"type": "long"},
                }
            },
        )

    # 文档索引
    if not client.indices.exists(index=KB_DOC_INDEX):
        client.indices.create(
            index=KB_DOC_INDEX,
            mappings={
                "properties": {
                    "uuid": {"type": "keyword"},
                    "kb_uuid": {"type": "keyword"},
                    "title": {"type": "text"},
                    "content": {"type": "text"},
                    "create_at": {"type": "long"},
                    "update_at": {"type": "long"},
                }
            },
        )

    # 向量索引（简单存 embedding 数组，向量检索逻辑在 Python 里自己算相似度）
    if not client.indices.exists(index=KB_DOC_EMBED_INDEX):
        client.indices.create(
            index=KB_DOC_EMBED_INDEX,
            mappings={
                "properties": {
                    "uuid": {"type": "keyword"},
                    "kb_uuid": {"type": "keyword"},
                    "doc_uuid": {"type": "keyword"},
                    "chunk": {"type": "text"},
                    "embedding": {"type": "dense_vector", "dims": 1536},
                    "create_at": {"type": "long"},
                }
            },
        )


# ==== 知识库 ====


def create_kb(doc: Dict[str, Any]) -> None:
    client = get_es_client()
    _ensure_indices(client)
    client.index(index=KB_INDEX, document=doc)


def update_kb(uuid: str, fields: Dict[str, Any]) -> None:
    client = get_es_client()
    _ensure_indices(client)
    # 查到 _id 再更新
    res = client.search(index=KB_INDEX, query={"term": {"uuid": uuid}})
    hits = res.get("hits", {}).get("hits", [])
    if not hits:
        return
    kb_id = hits[0]["_id"]
    client.update(index=KB_INDEX, id=kb_id, doc=fields)


def delete_kb(uuid: str) -> None:
    client = get_es_client()
    _ensure_indices(client)
    # 删除知识库本身
    res = client.search(index=KB_INDEX, query={"term": {"uuid": uuid}})
    hits = res.get("hits", {}).get("hits", [])
    for hit in hits:
        client.delete(index=KB_INDEX, id=hit["_id"])

    # 级联删除文档及向量
    client.delete_by_query(index=KB_DOC_INDEX, body={"query": {"term": {"kb_uuid": uuid}}})
    client.delete_by_query(index=KB_DOC_EMBED_INDEX, body={"query": {"term": {"kb_uuid": uuid}}})


def list_kb(page: int, size: int) -> Dict[str, Any]:
    client = get_es_client()
    _ensure_indices(client)
    res = client.search(
        index=KB_INDEX,
        from_=(page - 1) * size,
        size=size,
        sort=[{"create_at": {"order": "desc"}}],
        query={"match_all": {}},
    )
    total = res.get("hits", {}).get("total", {}).get("value", 0)
    items = [hit["_source"] for hit in res.get("hits", {}).get("hits", [])]
    return {"total": total, "list": items}


def get_kb(uuid: str) -> Optional[Dict[str, Any]]:
    client = get_es_client()
    _ensure_indices(client)
    res = client.search(index=KB_INDEX, query={"term": {"uuid": uuid}})
    hits = res.get("hits", {}).get("hits", [])
    if not hits:
        return None
    return hits[0]["_source"]


# ==== 文档 ====


def create_doc(doc: Dict[str, Any]) -> None:
    client = get_es_client()
    _ensure_indices(client)
    client.index(index=KB_DOC_INDEX, document=doc)


def update_doc(uuid: str, fields: Dict[str, Any]) -> None:
    client = get_es_client()
    _ensure_indices(client)
    res = client.search(index=KB_DOC_INDEX, query={"term": {"uuid": uuid}})
    hits = res.get("hits", {}).get("hits", [])
    if not hits:
        return
    doc_id = hits[0]["_id"]
    client.update(index=KB_DOC_INDEX, id=doc_id, doc=fields)


def delete_doc(uuid: str) -> None:
    client = get_es_client()
    _ensure_indices(client)
    # 删除文档
    res = client.search(index=KB_DOC_INDEX, query={"term": {"uuid": uuid}})
    hits = res.get("hits", {}).get("hits", [])
    for hit in hits:
        client.delete(index=KB_DOC_INDEX, id=hit["_id"])

    # 删除对应向量
    client.delete_by_query(
        index=KB_DOC_EMBED_INDEX,
        body={"query": {"term": {"doc_uuid": uuid}}},
    )


def list_docs(kb_uuid: str, page: int, size: int) -> Dict[str, Any]:
    client = get_es_client()
    _ensure_indices(client)
    res = client.search(
        index=KB_DOC_INDEX,
        from_=(page - 1) * size,
        size=size,
        sort=[{"create_at": {"order": "desc"}}],
        query={"term": {"kb_uuid": kb_uuid}},
    )
    total = res.get("hits", {}).get("total", {}).get("value", 0)
    items = [hit["_source"] for hit in res.get("hits", {}).get("hits", [])]
    return {"total": total, "list": items}


def get_doc(uuid: str) -> Optional[Dict[str, Any]]:
    client = get_es_client()
    _ensure_indices(client)
    res = client.search(index=KB_DOC_INDEX, query={"term": {"uuid": uuid}})
    hits = res.get("hits", {}).get("hits", [])
    if not hits:
        return None
    return hits[0]["_source"]


# ==== 向量 ====


def upsert_doc_embeddings(
    kb_uuid: str, doc_uuid: str, chunks_with_embeddings: List[Dict[str, Any]]
) -> None:
    """
    为文档写入/更新向量信息：
    - 先删掉原有 doc_uuid 对应的向量
    - 再批量写入新的
    """
    client = get_es_client()
    _ensure_indices(client)
    # 删除旧的
    client.delete_by_query(
        index=KB_DOC_EMBED_INDEX,
        body={"query": {"term": {"doc_uuid": doc_uuid}}},
    )
    # 写入新的
    for item in chunks_with_embeddings:
        body = {
            "uuid": item["uuid"],
            "kb_uuid": kb_uuid,
            "doc_uuid": doc_uuid,
            "chunk": item["chunk"],
            "embedding": item["embedding"],
            "create_at": item["create_at"],
        }
        client.index(index=KB_DOC_EMBED_INDEX, document=body)


def list_doc_embeddings(kb_uuid: str) -> List[Dict[str, Any]]:
    """
    获取某个知识库下的所有文档向量（简单实现：一次性拉取，适合小数据量）。
    """
    client = get_es_client()
    _ensure_indices(client)
    res = client.search(
        index=KB_DOC_EMBED_INDEX,
        size=1000,
        query={"term": {"kb_uuid": kb_uuid}},
    )
    hits = res.get("hits", {}).get("hits", [])
    return [hit["_source"] for hit in hits]


