from os import access

from fastapi import APIRouter, Depends

from app.auth import create_access_token, get_current_user
from app.model.kafe.member import Member
from app.request.BiometricRequest import BiometricRequest
from app.services.BiometricService import BiometricServiceInstance


router = APIRouter()
@router.post('/login')
def login_biometric(
      body:BiometricRequest,
      service:BiometricServiceInstance
):
    member=service.login_with_biometric(
        device_id=body.device_id,
        token_biometric=body.token_biometric
    )
    access_token=create_access_token(data={"sub":member.Username})
    return {"message": "Login endpoint", "access_token": access_token, "token_type": "bearer"}

@router.post('/register')
def reqister_biometric(
    body:BiometricRequest,
    service:BiometricServiceInstance,
    current_user: Member = Depends(get_current_user)
):
    member=service.register_device(
        username=current_user.Username,
        biometric_token=body.token_biometric,
        device_id=body.device_id
    )
    
    return {"message":"Berhasil Login"}
@router.delete('/logout')
def logout_biometric(
    service:BiometricServiceInstance,
    current_user: Member = Depends(get_current_user)
):
    service.revoke_device(
         username=current_user.Username,
    )  
    return {"message":"anda berhasil logout"}
@router.get('/status')
def status_biometric(
     service:BiometricServiceInstance,
    current_user:Member=Depends(get_current_user)
):
    
    return service.get_device_status(
        username=current_user.Username
    )