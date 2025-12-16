from fastapi import APIRouter

router = APIRouter()


@router.get("/ping", tags=["TRY"])
async def ping():
    """健康检查接口"""
    return "pong"

