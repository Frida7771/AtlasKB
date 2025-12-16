from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from service.admin.user import create_service, reset_password_service, list_service
from middleware.auth import get_current_user, UserClaim

router = APIRouter()


class UserCreateRequest(BaseModel):
    """创建用户请求"""
    username: str
    password: str
    email: Optional[str] = None


class UserResetPasswordRequest(BaseModel):
    """重置密码请求"""
    uuid: str
    password: str


@router.post("/user/create", tags=["超管模块-用户管理"])
async def create(
    req: UserCreateRequest,
    current_user: UserClaim = Depends(get_current_user)
):
    """创建用户"""
    success, error = create_service(req.username, req.password, req.email)
    if error:
        return {"code": -1, "msg": error}
    return {"code": 200, "msg": "创建成功"}


@router.post("/user/reset/password", tags=["超管模块-用户管理"])
async def reset_password(
    req: UserResetPasswordRequest,
    current_user: UserClaim = Depends(get_current_user)
):
    """重置密码"""
    success, error = reset_password_service(req.uuid, req.password)
    if error:
        return {"code": -1, "msg": error}
    return {"code": 200, "msg": "重置成功"}


@router.get("/user/list", tags=["超管模块-用户管理"])
async def list(
    page: int = Query(1, description="当前页"),
    size: int = Query(10, description="每页的数据条数"),
    current_user: UserClaim = Depends(get_current_user)
):
    """用户列表"""
    result, error = list_service(page, size)
    if error:
        return {"code": -1, "msg": error}
    return {"code": 200, "data": result}

