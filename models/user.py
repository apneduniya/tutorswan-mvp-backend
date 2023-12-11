from pydantic import BaseModel

class UserBase(BaseModel):
    id: str
    name: str
    email: str
    password: str
    role: str # like client, admin
    plan: str
    # Add more fields as per your user requirements

class TempUserBase(BaseModel):
    name: str
    instituteName: str
    userName: str
    email: str
    password: str
    nosStudents: int
    nosSemesters: int
    nosSubjects: int

class UserResponse(BaseModel):
    id: str
    name: str
    phone_number: str
    email: str
    role: str
    plan: str

class UserCreate(BaseModel):
    name: str
    phone_number: str
    email: str
    password: str

class User(BaseModel):
    id: str

class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    role: str

class TokenData(BaseModel):
    username: str = None


class GetUserDataLimit(BaseModel):
    limit: int = 10


class AmountUserId(BaseModel):
    amount: int
    user_id: str

