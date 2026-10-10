from datetime import datetime

from sqlmodel import SQLModel, Field, default
from sqlalchemy import Column, Integer

from app.services.firebase_service import FirebaseService

class Login(SQLModel, table=True):
    __tablename__ = "login"
    User: str = Field(default=None, primary_key=True,)
    Username: str | None = Field(default=None)
    Tingkat: str | None = Field(default=None)
    IDMember: str |None = Field(default = None, primary_key=True)
    Password: str | None = Field(default=None)
    Active: str | None = Field(default=None)
    DeviceId: str | None = Field(default=None)
    TokenBiometric: str | None = Field(default=None)
    TokenOtp: str | None = Field(default=None)
    TokenAttempOtp: int | None = Field(default=None)
    TokenExpiredDateOtp: str | None = Field(default=None)
    EmailVerified : datetime | None = Field(default=None)
    Email : str | None = Field(default= None)
    