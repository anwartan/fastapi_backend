from pydantic import BaseModel

class ForgotPasswordRequest(BaseModel):
    email: str
    new_password:str