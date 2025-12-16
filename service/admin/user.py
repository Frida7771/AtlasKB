import uuid
from datetime import datetime
from typing import Optional

import bcrypt

from dao.user_basic_dao import (
    search_user_by_username,
    search_user_by_uuid,
    create_user,
    update_user,
    list_users,
)
from models.user_basic import UserBasicDao


def _hash_password(plain_password: str) -> str:
    """
    使用 bcrypt 对密码进行哈希
    """
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )


def create_service(username: str, password: str, email: Optional[str] = None) -> tuple[bool, Optional[str]]:
    """
    创建用户服务
    返回: (success, error_message)
    """
    # 1. 检查用户名是否存在
    response = search_user_by_username(username)
    total = response.get("hits", {}).get("total", {}).get("value", 0)
    if total > 0:
        return False, "用户名已存在"
    
    # 2. 创建用户（密码哈希存储）
    now = int(datetime.utcnow().timestamp() * 1000)
    user = UserBasicDao(
        uuid=str(uuid.uuid4()),
        username=username,
        password=_hash_password(password),
        email=email,
        create_at=now,
        update_at=now
    )
    create_user(user)
    
    return True, None


def reset_password_service(user_uuid: str, password: str) -> tuple[bool, Optional[str]]:
    """
    重置密码服务
    返回: (success, error_message)
    """
    # 1. 获取用户信息
    response = search_user_by_uuid(user_uuid)
    
    hits = response.get("hits", {}).get("hits", [])
    if not hits:
        return False, "获取用户信息失败"
    
    user_id = hits[0]["_id"]
    
    # 2. 更新密码（密码哈希存储）
    update_user(user_id, {
        "password": _hash_password(password),
        "update_at": int(datetime.utcnow().timestamp() * 1000)
    })
    
    return True, None


def list_service(page: int, size: int) -> tuple[Optional[dict], Optional[str]]:
    """
    获取用户列表服务
    返回: (result, error_message)
    """
    try:
        response = list_users(page, size)
        
        total = response.get("hits", {}).get("total", {}).get("value", 0)
        hits = response.get("hits", {}).get("hits", [])
        
        user_list = []
        for hit in hits:
            user_source = hit["_source"]
            user_basic = UserBasicDao(**user_source)
            user_list.append(user_basic.dict())
        
        return {
            "list": user_list,
            "total": total
        }, None
    except Exception as e:
        return None, str(e)

