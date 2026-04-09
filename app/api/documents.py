from fastapi import APIRouter, HTTPException, Depends, Request, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import os
import uuid
import aiofiles
from app.models.document import Document, DocumentStatus
from app.core.security import hash_password, verify_password, create_access_token
from app.database import get_db
from app.schemas.document import DocumentResponse
from app.schemas.user import TokenResponse, UserRegister, UserResponse, UserLogin
from app.models.user import User
from sqlalchemy import select
from app.api.deps import get_current_user
from app.tasks.process_document import process_document
from app.services.document_service import service
from app.core.exceptions import UnsupportedFileType, FileUploadError, DocumentNotFound, NotAllowedToDelete

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        result = await service.upload_document(file=file, db=db, current_user=current_user)
    except UnsupportedFileType as e:
        raise HTTPException(status_code=415, detail=str(e))
    except FileUploadError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return result


@router.get("", response_model=list[DocumentResponse], status_code=200)
async def get_documents(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return await service.get_documents(db=db, current_user=current_user)


@router.delete("/{document_id}", status_code=204)
async def delete_document(
        document_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        result = await service.delete_document(document_id=document_id, db=db, current_user=current_user)
    except DocumentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotAllowedToDelete as e:
        raise HTTPException(status_code=403, detail=str(e))

    return result




