from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

import bcrypt
from jose import JWTError, jwt

from src.core.config import settings


# Проверяет совпадение открытого пароля с его bcrypt-хешем
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )
    
# Генерирует безопасный bcrypt-хеш для пароля
def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    pwd_bytes = password.encode("utf-8")
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def create_access_token(
    subject: Union[str, int],
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[dict[str, Any]] = None,
) -> str:
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "access",
    }
    
    if extra_claims:
        to_encode.update(extra_claims)
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt

# Создает jwt токен для обновления сессии
def create_refresh_token(
    subject: Union[str, int],
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "refresh",
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    
    return encoded_jwt

# Декодирует и проверяет валидность jwt-токена
def decode_token(token: str) -> Optional[dict[str, Any]]:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        return None
