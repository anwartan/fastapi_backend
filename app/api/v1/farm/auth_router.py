

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from app.api.v1.farm.farm_service.auth_farm_service import AuthFarmService, AuthServiceInstance
from app.api.v1.farm.request.forgetpass_request import VerifyForget
from app.api.v1.farm.request.login_request import LoginRequest
from app.api.v1.farm.request.verify_email_request import VerifyEmailRequest
from app.auth import create_access_token, get_current_user, get_current_user_farm
from app.database import SessionDB1
from app.model.farm.login import Login
from app.request import forget_password_request



router = APIRouter()
@router.post("/login")
def login(data: LoginRequest, session: SessionDB1):
    login_query = select(Login).where(Login.Username == data.Username)
    user = session.exec(login_query).first()
    if user is None:
        raise HTTPException(status_code=400, detail="Username tidak ditemukan")
    if user.Password != data.Password:
        raise HTTPException(status_code=400, detail="Password tidak valid")
    access_token = create_access_token(data={"sub": user.Username})
    return {
        "access_token": access_token, "token_type": "bearer"
    }
@router.get("/me")
def read_user_me(current_user = Depends(get_current_user_farm)):
    return{"data": current_user}

@router.get("/send-verification-email/{email}")
async def get_auth_router(email: str, authService: AuthServiceInstance, get_current_user= Depends(get_current_user_farm) ):
    await authService.sendEmailVerification(email, get_current_user['Username'])
    return {"message": "verification email sent"}
@router.post("/verify-email")
def verify_email (request: VerifyEmailRequest, authService: AuthServiceInstance, get_current_user= Depends(get_current_user_farm)):
    authService.verify_email(get_current_user['Username'], request.email, request.code)
    return {"message": "Email verified successfully"}

def logout(current_user = Depends(get_current_user_farm)):
    return False

@router.get("/forgetpass/{email}")
async def SendForgetPassword(email: str, authService: AuthServiceInstance):
    await authService.sendforgetpass(email)
    return {"message": "berhasil"}
@router.post("verifyforgetpass")
async def VerifyForgetPassword(request: VerifyForget, authService: AuthServiceInstance):
    await authService.sendforgetpass()
    return {"message": "berhasil"}
    
