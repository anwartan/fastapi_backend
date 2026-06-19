
from pydantic import BaseModel, field_validator


class ChangePasswordRequest(BaseModel):
    username: str
    new_password:str
    @field_validator('username')
    def validate_username(cls, value):
        if len(value) < 3:
            raise ValueError('Username must be at least 3 characters long')
        return value    
    
     
    @field_validator('new_password')
    def validate_new_password(cls,value):
        if len(value) < 6:
            raise ValueError('New Password Must be at least 6 character long')
        return value