from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    org_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: EmailStr
    role: str
    org_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ApiKeyCreateResponse(BaseModel):
    id: str
    name: str
    key: str  # full key — shown ONCE at creation time only
    key_prefix: str


class ApiKeyOut(BaseModel):
    id: str
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: datetime | None
    revoked: bool

    class Config:
        from_attributes = True
