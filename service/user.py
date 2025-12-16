from jose import jwt

from datetime import datetime, timedelta
from typing import Optional

import bcrypt

from dao.user_basic_dao import search_user_by_username, update_user
from models.user_basic import UserBasicDao
from define import JWT_SECRET
from service.admin.user import create_service as admin_create_service


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    校验密码（支持新老两种存储方式）：
    - 新：bcrypt 哈希
    - 旧：明文（兼容之前已有数据）
    """
    # 旧数据：明文存储，直接比对
    if not hashed_password.startswith("$2b$") and not hashed_password.startswith("$2a$"):
        return plain_password == hashed_password

    # 新数据：bcrypt 哈希
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def login_service(username: str, password: str) -> tuple[Optional[str], Optional[str]]:
    """
    登录服务
    返回: (token, error_message)
    """
    # 1. 获取用户信息
    response = search_user_by_username(username)
    
    hits = response.get("hits", {}).get("hits", [])
    if not hits:
        return None, "用户名不存在"
    
    # 2. 解析用户数据
    user_source = hits[0]["_source"]
    user_basic = UserBasicDao(**user_source)
    
    # 3. 校验密码（支持哈希）
    if not _verify_password(password, user_basic.password):
        return None, "密码不正确"
    
    # 4. 生成 token
    exp = datetime.utcnow() + timedelta(days=1)
    claim = {
        "uuid": user_basic.uuid,
        "username": user_basic.username,
        "email": user_basic.email,
        "exp": int(exp.timestamp())  # PyJWT 使用秒，不是毫秒
    }
    token = jwt.encode(claim, JWT_SECRET, algorithm="HS256")
    
    return token, None


def register_service(
    username: str, password: str, email: Optional[str]
) -> tuple[bool, Optional[str]]:
    """
    普通用户注册，复用管理员创建逻辑（包含用户名唯一校验与密码哈希）。
    """
    return admin_create_service(username, password, email)


def password_modify_service(user_uuid: str, username: str, old_password: str, new_password: str) -> tuple[bool, Optional[str]]:
    """
    修改密码服务
    返回: (success, error_message)
    """
    # 1. 获取用户信息
    response = search_user_by_username(username)
    
    hits = response.get("hits", {}).get("hits", [])
    if not hits:
        return False, "用户名不存在"
    
    user_id = hits[0]["_id"]
    user_source = hits[0]["_source"]
    user_basic = UserBasicDao(**user_source)
    
    # 2. 校验用户 UUID
    if user_basic.uuid != user_uuid:
        return False, "用户信息不匹配"
    
    # 3. 校验旧密码（支持哈希）
    if not _verify_password(old_password, user_basic.password):
        return False, "旧密码不正确"
    
    # 4. 更新密码
    from datetime import datetime
    update_user(
        user_id,
        {
            # 新密码一律以哈希存储
            "password": bcrypt.hashpw(
                new_password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8"),
            "update_at": int(datetime.utcnow().timestamp() * 1000),
        },
    )
    
    return True, None

