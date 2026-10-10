from pydantic import BaseModel, field_validator
class LoginRequest(BaseModel):
    Username: str
    Password: str

    @field_validator("Username")
    def username_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("Username must not be empty")
        return v

    @field_validator("Password")
    def password_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("Password must not be empty")
        return v