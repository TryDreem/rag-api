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
from app.core.exceptions import UnsupportedFileType, FileUploadError
from app.tasks.process_document import process_document

logger = logging.getLogger(__name__)


class DocumentService:
    async def upload_document(self, file: UploadFile, db: AsyncSession, current_user: User):
        filename = f"{uuid.uuid4()}_{file.filename}"
        logger.info(f"Trying to upload file: {filename}")

        if file.content_type != "application/pdf":
            logger.info(f"Unsupported file type: {file.content_type}")
            raise UnsupportedFileType("Unsupported Content-Type")

        os.makedirs("uploads", exist_ok=True)
        path = f"uploads/{filename}"

        try:
            async with aiofiles.open(path, "wb") as f:
                content = await file.read()
                await f.write(content)

            logger.info(f"Uploaded file: {filename}")

        except FileNotFoundError:
            raise FileUploadError("File not found")

        db_document = Document(
            user_id=current_user.id,
            filename=filename,
            status=DocumentStatus.pending,
        )

        db.add(db_document)
        await db.commit()
        await db.refresh(db_document)

        process_document.delay(
            document_id=db_document.id,
            file_path=path
        )

        return DocumentResponse.model_validate(db_document)


service = DocumentService()