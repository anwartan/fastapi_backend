from pydantic import BaseModel, field_validator


class VerifyForget(BaseModel):
    password: str
    code: str
    
    @field_validator("password")
    def validator_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email address")
        return v
    
    @field_validator("code")
    def validator_code(cls, v):
        if len(v) != 6 or not v.isdigit():
            raise ValueError("invalid code")
        return v