from typing import Optional
from pydantic import BaseModel, EmailStr, constr, ConfigDict


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: constr(min_length=3, max_length=50)
    first_name: Optional[str] = None
    last_name: Optional[str] = None



class UserResponse(BaseModel):
    id: int
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    owner_id: int
    date: Optional[str] = None
    time: Optional[str] = None
    completed: bool = False

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    completed: Optional[bool] = False
  

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    owner_id: int
    date: Optional[str] = None
    time: Optional[str] = None
    completed: bool
    
    model_config = ConfigDict(from_attributes=True)
