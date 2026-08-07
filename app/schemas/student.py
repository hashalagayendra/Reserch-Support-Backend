from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional

class StudentBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    age: Optional[int] = None
    is_active: bool = True

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    age: Optional[int] = None
    is_active: Optional[bool] = None

class StudentResponse(StudentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
