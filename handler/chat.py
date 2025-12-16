from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query, HTTPException

from middleware.auth import get_current_user, UserClaim
from models.chat import ChatCreate, ChatMessageCreate, ChatReply, ChatMessage
from service import chat as chat_service

router = APIRouter(tags=["Chat模块"])


@router.post("/chat", summary="创建对话")
async def create_chat(
    req: ChatCreate,
    current_user: UserClaim = Depends(get_current_user),
) -> Dict[str, Any]:
    chat = chat_service.create_chat_service(current_user.uuid, req)
    return {"code": 200, "data": chat}


@router.get("/chat/list", summary="对话列表")
async def list_chats(
    page: int = Query(1, description="当前页"),
    size: int = Query(10, description="每页条数"),
    current_user: UserClaim = Depends(get_current_user),
) -> Dict[str, Any]:
    data = chat_service.list_chats_service(current_user.uuid, page, size)
    return {"code": 200, "data": data}


@router.delete("/chat/{chat_uuid}", summary="删除对话")
async def delete_chat(
    chat_uuid: str,
    current_user: UserClaim = Depends(get_current_user),
) -> Dict[str, Any]:
    ok = chat_service.delete_chat_service(current_user.uuid, chat_uuid)
    if not ok:
        raise HTTPException(status_code=404, detail={"code": 404, "msg": "对话不存在"})
    return {"code": 200, "msg": "删除成功"}


@router.get("/chat/{chat_uuid}/messages", summary="消息列表", response_model=List[ChatMessage])
async def list_messages(
    chat_uuid: str,
    current_user: UserClaim = Depends(get_current_user),
) -> List[ChatMessage]:
    messages = chat_service.list_messages_service(current_user.uuid, chat_uuid, limit=100)
    if not messages:
        # 可能是对话不存在或无权限
        chat = chat_service.get_chat(chat_uuid) if hasattr(chat_service, "get_chat") else None
        if not chat:
            raise HTTPException(status_code=404, detail={"code": 404, "msg": "对话不存在"})
    return messages


@router.post("/chat/{chat_uuid}/message", summary="发送消息", response_model=ChatReply)
async def send_message(
    chat_uuid: str,
    req: ChatMessageCreate,
    current_user: UserClaim = Depends(get_current_user),
) -> ChatReply:
    reply = chat_service.send_message_service(current_user.uuid, chat_uuid, req)
    if not reply:
        raise HTTPException(status_code=404, detail={"code": 404, "msg": "对话不存在"})
    return reply


