
from sqlmodel import select

from fastapi import APIRouter, Depends,HTTPException 

from app.services.AuthService import AuthService, AuthServiceInstance
from app.services.email_service import send_otp_email
from app.auth import create_access_token, get_current_user, get_password_hash
from app.model.kafe.member import Member
from app.database import SessionDBKafe, SessionDBKafeLogin
from app.request.LoginRequest import LoginRequest
from app.request.ceateuserrequest import CreateuserRequest
from app.request.change_password_request import ChangePasswordRequest
from app.request.forget_password_request import ForgotPasswordRequest
from app.request.verify_otp_request import VerifyOtpRequest
from app.services.veriyemail import VerifyEmail

router=APIRouter()
@router.post("/register")
def register(formdata: CreateuserRequest, session: SessionDBKafe):
    new_user = {
        "User": formdata.fullname,
        "Username": formdata.username,
        "PW": get_password_hash(formdata.password),
        "Tingkat": "Basic"
    }
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return {"message": "User registered successfully"}
@router.post("/login")
def user_login(formdata: LoginRequest, session: SessionDBKafeLogin):
    username=formdata.username
    user=select(Member).where(Member.Username==username)
    user=session.exec(user).first() 
    if user == None:
        raise HTTPException(status_code=404, detail="")
    # verify_password=verify_password(formdata.password, user.PW)
    verify_password=formdata.password == user.PW
    if not verify_password:
        return {"message": "Invalid username or password"}
    if user.Active != 1:
        raise HTTPException(status_code=403, detail="User is not active")
    access_token = create_access_token(data={"sub": user.Username}, 
    )
    return {"message": "Login endpoint", "access_token": access_token, "token_type": "bearer"}
@router.get("/user/me")
def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user



@router.put("/changepassword")
def change_password(
    request:ChangePasswordRequest,
    session: SessionDBKafeLogin
):

    user = session.exec(
        select(Member).where(Member.Username == request.username)
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    

    user.PW = request.new_password

    session.add(user)
    session.commit()

    return {"message": "Password berhasil diubah"}



@router.get("/send-verification/{email}")
async def get_auth_router(
        email:str,
        authservice: AuthServiceInstance,
        current_user: Member = Depends(get_current_user)
):
    await authservice.SendVerifyEmail(email,current_user.Username)
    return{"message":"Kode sudah tterkirim ke email anda"}
@router.post("/verify-email")
def verify_email(req:VerifyEmail, authService:AuthServiceInstance,
                 current_user: Member = Depends(get_current_user)
    ):
    authService.VerifyEmail(req.email,current_user.Username, req.code)
    return{"message":"berhasil verifikasi"}