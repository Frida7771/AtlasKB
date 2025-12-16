from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from service.user import login_service, password_modify_service, register_service
from middleware.auth import get_current_user, UserClaim

router = APIRouter()


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    username: str
    password: str


class PasswordModifyRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str


class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    username: str
    password: str
    email: str | None = None


@router.post("/login", tags=["用户模块"])
async def login(req: UserLoginRequest):
    """用户登录"""
    token, error = login_service(req.username, req.password)
    if error:
        return {"code": -1, "msg": error}
    return {"code": 200, "data": {"token": token}}


@router.post("/register", tags=["用户模块"])
async def register(req: UserRegisterRequest):
    """用户注册"""
    success, error = register_service(req.username, req.password, req.email)
    if error or not success:
        return {"code": -1, "msg": error or "注册失败"}
    return {"code": 200, "msg": "注册成功"}


@router.post("/password/modify", tags=["用户模块"])
async def password_modify(
    req: PasswordModifyRequest,
    current_user: UserClaim = Depends(get_current_user)
):
    """修改密码"""
    success, error = password_modify_service(
        current_user.uuid,
        current_user.username,
        req.old_password,
        req.new_password
    )
    if error:
        return {"code": -1, "msg": error}
    return {"code": 200, "msg": "修改成功"}

