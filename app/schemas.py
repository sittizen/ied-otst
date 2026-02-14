from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.models import AccountType


class GMRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    display_name: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class WhoAmIResponse(BaseModel):
    id: str
    email: EmailStr
    display_name: str
    account_type: AccountType
