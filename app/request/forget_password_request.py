from pydantic import BaseModel

class ForgotPasswordRequest(BaseModel):
    username: str
    email: str