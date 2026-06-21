
from datetime import datetime
from enum import member

from fastapi.templating import Jinja2Templates
from sqlmodel import Session,select
from app.database import SessionDBKafeLogin,get_session_kafe_login
from typing import Annotated
from fastapi import Depends, HTTPException
from app.model.kafe.member import Member
from fastapi_mail import MessageSchema,MessageType
from app.mail import Mail
from app.services import otp_service
from app.services.otp_service import OtpServiceInstance
class AuthService:
    def __init__(self,session:SessionDBKafeLogin,mail:Mail,otp_service:OtpServiceInstance):
        self.session=session
        self.mail=mail
        self.otp_service=otp_service
        self.templates=Jinja2Templates(directory="app/templates")
    async def SendVerifyEmail(self,email:str,username:str):
        member_statement=select(Member).where(Member.Username==username)
        members=self.session.exec(member_statement).first()
        if not members:
              raise Exception("Member tidak ada")
        otp=self.otp_service.createotp(username)
        html_content=self.templates.get_template("send_verification.html").render(
              nama=members,
              otp=otp,
              expire_minutes=self.otp_service.Max_attempt
            
        )
        message=MessageSchema(
            subject="Email Verify",
            recipients=[email],
            body=html_content,
            subtype=MessageType.html
        )
        await self.mail.send_message(message)
    def VerifyEmail(self,email:str,username: str, code:str):
        is_valid=self.otp_service.verify_otp(code, username)
        if not is_valid:
             raise HTTPException(status_code=400, detail="invalid or expired OTP")
        member_statement=select(Member).where(Member.Username==username)
        members=self.session.exec(member_statement).first()
        if not members:
              raise HTTPException(status_code=404, detail="Member is not found")
        members.Email=email
        members.VerifyDate = datetime.now()
        self.session.add(members)
        self.session.commit()
def get_auth_service(session:SessionDBKafeLogin, mail:Mail,otp_service : OtpServiceInstance) -> AuthService:
    return AuthService(session,mail,otp_service)
    
AuthServiceInstance = Annotated[AuthService, Depends(get_auth_service)]