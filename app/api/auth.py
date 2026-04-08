from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.security import hash_password, verify_password, create_access_token
from app.database import get_db
from app.schemas.user import TokenResponse, UserRegister, UserResponse, UserLogin
from app.models.user import User
from sqlalchemy import select
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user: UserRegister,db: AsyncSession = Depends(get_db)):
    query = select(User).where(User.email == user.email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        logger.warning(f"User {user.email} already exists")
        raise HTTPException(status_code=409, detail=f"User {user.email} already exists")

    hashed_password = hash_password(user.password)

    db_user = User(
        email=user.email,
        password=hashed_password,
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    logger.info(f"User {user.email} registered")

    return UserResponse.model_validate(db_user)


@router.post("/login", response_model=TokenResponse, status_code=200)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    logger.info(f"User {credentials.email} logging in")
    query = select(User).where(User.email == credentials.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        logger.info(f"User {credentials.email} not found")
        raise HTTPException(status_code=404, detail=f"User {credentials.email} not found")

    if not verify_password(credentials.password, user.password):
        logger.info(f"User {credentials.email} password incorrect")
        raise HTTPException(status_code=401, detail=f"Email or password incorrect")

    if not user.is_confirmed:
        logger.info(f"User {credentials.email} not confirmed")
        raise HTTPException(status_code=404, detail="User is not confirmed")

    access_token = create_access_token(email=user.email)

    return TokenResponse(access_token=access_token)


@router.post("/confirm-dev/{email}", status_code=200)
async def confirm_dev(email: str, db: AsyncSession = Depends(get_db)):
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        logger.info(f"User {email} not found")
        raise HTTPException(status_code=404, detail=f"User {email} not found")

    user.is_confirmed = True

    await db.commit()

    return {"message": "Email confirmed"}


@router.get("/me", response_model=UserResponse, status_code=200)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    logger.info(f"User {current_user.email} getting info")
    return UserResponse.model_validate(current_user)
