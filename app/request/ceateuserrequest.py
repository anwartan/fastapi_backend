
from pydantic import BaseModel, field_validator


class CreateuserRequest(BaseModel):
    username: str
    fullname: str
    password: str
    konfirmasi_password: str
    

    @field_validator('password')
    def validate_password(cls, value):
        if len(value) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return value
    @field_validator('username')
    def validate_username(cls, value):
        if len(value) < 3:
            raise ValueError('Username must be at least 3 characters long')
        return value
    @field_validator('konfirmasi_password')
    def validate_konfirmasi_password(cls, value, values):
        if 'password' in values and value != values['password']:
            raise ValueError('Password and konfirmasi_password do not match')
        return value
    @field_validator('fullname')
    def validate_fullname(cls, value):
        if len(value) < 3:
            raise ValueError('Fullname must be at least 3 characters long')
        return value