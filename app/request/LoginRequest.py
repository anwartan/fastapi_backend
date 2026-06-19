
from pydantic import BaseModel, field_validator


class LoginRequest(BaseModel):
    username: str
    password: str
    @field_validator('username')
    def validate_username(cls, value):
        if len(value) < 3:
            raise ValueError('Username must be at least 3 characters long')
        return value    
    
    @field_validator('password')
    def validate_password(cls, value):
        if len(value) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return value
    