from sqlmodel import Session,select
from app.database import SessionDBKafeLogin,get_session_kafe_login
from typing import Annotated
from fastapi import Depends
from app.model.kafe.member import member
from fastapi_mail import MessageSchema,MessageType
from app.mail import Mail
class AuthService:
    def __init__(self,session:SessionDBKafeLogin,mail:Mail):
        self.session=session
        self.mail=mail
    async def SendVerifyEmail(self,email:str):
        member_statement=select(member).where(member.Email==email)
        members=self.session.exec(member_statement).first
        if not members:
              raise Exception("Member tidak ada")
        message=MessageSchema(
            subject="Email Verify",
            recipients=[email],
            body="Emwekfmwmnfwron",
            subtype=MessageType.html
        )
        await self.mail.send_message(message)
    def VerifyEmail(self,email:str,code:str):
                return ""
def get_auth_service(session:SessionDBKafeLogin, mail:Mail) -> AuthService:
    return AuthService(session,mail)
    
AuthServiceInstance = Annotated[AuthService, Depends(get_auth_service)]