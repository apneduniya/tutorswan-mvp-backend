# from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Tuple
from models.user import UserCreate, TokenSchema, UserBase
from database.user import UserDB
from database.transactions import TransactionsDB
import datetime
from utils.helpers import helpers_single, helpers_multiple
from utils.user import (
    get_hashed_password,
    create_access_token,
    create_refresh_token,
    verify_password,
    get_current_active_user,
    is_admin
)

router = APIRouter()
user_db = UserDB()
transaction_db = TransactionsDB()


@router.post('/create', summary="Create new user", response_model=TokenSchema)
async def create_user(data: UserCreate):
    # querying database to check if user already exist
    user = user_db.get_user_email(data.email)
    if user is not None:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exist"
        )
    print(data)
    external_data :dict = {**data.dict()}
    external_data["role"] = "teacher"
    external_data.pop("password") # Doesn't saving raw password (orginal password)
    external_data["role"] = external_data["role"].lower()
    external_data["created_at"] = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    user_data = {
        'password': get_hashed_password(data.password), # Saving hashed password (for later verification)
        **external_data
    }
    user_id = user_db.create_user(user_data)    # saving user to database
    # return {"id": user_id, **data.dict()
    return {
        "access_token": create_access_token(user_data['email']),
        "refresh_token": create_refresh_token(user_data['email']),
        "role": user_data['role'],
    }
    

@router.post('/login', summary="Create access token for user", response_model=TokenSchema)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = user_db.get_user_email(form_data.username) # form_data.username is the email id of the user
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )

    hashed_pass = user['password']
    if not verify_password(form_data.password, hashed_pass):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    
    return {
        "access_token": create_access_token(user['email']),
        "refresh_token": create_refresh_token(user['email']),
        "role": user['role'],
    }


@router.get("/me")
async def read_users_me(
    current_user: UserBase = Depends(get_current_active_user)
):
    del current_user["password"]
    # print(current_user)
    return helpers_single(current_user)

@router.get("/data/{limit}/{id}")
async def read_users_me(
    current_user: UserBase = Depends(is_admin),
    limit: int = 10,
    id: str = None
):
    print(id)
    users_list = user_db.get_all_user(id=id, limit=limit)
    if not users_list:
        raise HTTPException(status_code=404, detail="Users not found")
    # print(users_list)
    return helpers_multiple(users_list)

