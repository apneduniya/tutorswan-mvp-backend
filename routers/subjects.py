# from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Tuple
from models.user import UserBase
from models.subjects import SubjectBase
from database.user import UserDB
import datetime
from utils.helpers import helpers_single, helpers_multiple
from utils.user import (
    get_current_active_user,
    is_admin
)

router = APIRouter()
user_db = UserDB()


@router.post('/create', summary="Create new subject")
async def create_subject(data: SubjectBase, current_user: UserBase = Depends(get_current_active_user)):
    user_db.create_new_subject(current_user["_id"], data.name)
    return {"message": "Subject created successfully"}





