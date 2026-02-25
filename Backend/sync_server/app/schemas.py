from pydantic import BaseModel, EmailStr
from typing import Optional, List, Union
from datetime import datetime, date
from uuid import UUID


class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    task_type_id: int
    personal_priority: int
    influence: int
    created_at: datetime
    deadline: Optional[datetime] = None
    final_priority: str
    status: str
    updated_at: datetime

class TaskCreate(TaskBase):
    pass

class TaskResponse(TaskBase):
    class Config:
        from_attributes = True

class SyncData(BaseModel):
    tasks: List[TaskCreate]

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class PullResponse(BaseModel):
    tasks: List[TaskResponse]
    server_time: str