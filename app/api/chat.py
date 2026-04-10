from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.exceptions import DocumentNotFound, UnsupportedFileType, AccessDenied
from app.schemas.chat import ChatResponse, ChatRequest, MessageResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.database import get_db
from app.schemas.user import TokenResponse, UserRegister, UserResponse, UserLogin
from app.models.user import User
from sqlalchemy import select
from app.api.deps import get_current_user
from app.services.chat_service import service
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/{document_id}", response_model=ChatResponse, status_code=201)
async def ask_question(
        document_id: int,
        question:ChatRequest,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        result = await service.ask_question(document_id=document_id, question=question.question, db=db, current_user=current_user)
    except DocumentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AccessDenied as e:
        raise HTTPException(status_code=403, detail=str(e))

    return ChatResponse(answer=result)


@router.get("/{document_id}/history", response_model=list[MessageResponse], status_code=200)
async def get_history(
        document_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        result = await service.get_history(document_id=document_id, db=db, current_user=current_user)
    except DocumentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AccessDenied as e:
        raise HTTPException(status_code=403, detail=str(e))

    return [MessageResponse.model_validate(message) for message in result]





