from typing import List, Optional
from pydantic import BaseModel, Field


class OTPRequest(BaseModel):
    mobile_number: str = Field(..., pattern=r"^\+?[1-9]\d{9,14}$", examples=["+919876543210"])


class OTPResponse(BaseModel):
    success: bool
    message: str
    delivery_channel: str
    expires_in_seconds: int = 300
    demo_hint: str


class OTPVerifyRequest(BaseModel):
    mobile_number: str
    otp_code: str = Field(..., min_length=4, max_length=6)


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    role: str


class TokenPayload(BaseModel):
    sub: str
    role: str
    exp: int
    type: str
