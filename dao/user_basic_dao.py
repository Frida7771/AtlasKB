from elasticsearch import Elasticsearch
from dao.init import get_es_client
from models.user_basic import UserBasicDao, USER_BASIC_DAO_INDEX


def search_user_by_username(username: str) -> dict:
    """根据用户名搜索用户"""
    client = get_es_client()
    response = client.search(
        index=USER_BASIC_DAO_INDEX,
        query={
            "term": {
                "username.keyword": username
            }
        }
    )
    return response


def search_user_by_uuid(uuid: str) -> dict:
    """根据 UUID 搜索用户"""
    client = get_es_client()
    response = client.search(
        index=USER_BASIC_DAO_INDEX,
        query={
            "term": {
                "uuid.keyword": uuid
            }
        }
    )
    return response


def create_user(user: UserBasicDao) -> dict:
    """创建用户"""
    client = get_es_client()
    response = client.index(
        index=USER_BASIC_DAO_INDEX,
        document=user.dict()
    )
    return response


def update_user(user_id: str, update_data: dict) -> dict:
    """更新用户"""
    client = get_es_client()
    response = client.update(
        index=USER_BASIC_DAO_INDEX,
        id=user_id,
        doc=update_data
    )
    return response


def list_users(page: int, size: int) -> dict:
    """获取用户列表"""
    client = get_es_client()
    response = client.search(
        index=USER_BASIC_DAO_INDEX,
        size=size,
        from_=(page - 1) * size,
        sort=[
            {
                "create_at": {
                    "order": "desc"
                }
            }
        ],
        query={
            "match_all": {}
        }
    )
    return response

