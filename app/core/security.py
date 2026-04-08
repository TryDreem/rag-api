from datetime import datetime, timedelta
from app.core.config import settings
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import HTTPException

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        'sub': email,
        'exp': expire,
        'type': "access"
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return token

def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        token_type = payload.get('type')
        if token_type != "access":
            raise HTTPException(status_code=403, detail="Invalid token")

        email = payload.get('sub')
        if not email:
            raise HTTPException(status_code=403, detail="Invalid token")

        return email

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")