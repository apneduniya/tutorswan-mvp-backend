from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Union, Any, Tuple
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from fastapi import Depends, HTTPException
from starlette import status
from models.user import (
    TokenData,
    UserBase
)
from database.user import (
    UserDB
)


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")

ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days
ALGORITHM = "HS256"
JWT_SECRET_KEY = "hwlpUxqoygef3592876e68/ON*$FYN2ry3gfb893/Fnku"# should be kept secret
JWT_REFRESH_SECRET_KEY = "KUYTNE@ILYEN@fgo7t*N^@ioyqxnti672I&Etdoeuwf=F"    # should be kept secret


def get_hashed_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, hashed_pass: str) -> bool:
    return password_context.verify(password, hashed_pass)


def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, ALGORITHM)
    return encoded_jwt


user_db = UserDB()


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            payload = jwt.decode(token, JWT_REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            # print("username is None")
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        # print("JWTError")
        raise credentials_exception
    user = user_db.get_user_email(email=token_data.username)
    if user is None:
        # print("user is None")
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: UserBase = Depends(get_current_user)
):
    if current_user["role"] == "disabled":
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def is_admin(
    current_user: UserBase = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=400, detail="Not an admin")
    return current_user
