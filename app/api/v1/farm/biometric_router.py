

from fastapi import APIRouter, Depends

from app.api.v1.farm.farm_service.BiometricService import BiometricService, BiometricServiceInstance
from app.api.v1.farm.request.biometric_request import BiometricRegisterRequest
from app.api.v1.farm.request.biometric_request import BiometricLoginRequest
from app.auth import create_access_token, get_current_user_farm
from app.model.kafe.member import Member


router = APIRouter()

@router.post('/register')
def register_biometric(
    body: BiometricRegisterRequest,
    biometric_service: BiometricServiceInstance,
    current_user: dict = Depends(get_current_user_farm),
):
    biometric_service.register_device(
        username=current_user["Username"],
        device_id=body.device_id,
        biometric_token=body.biometric_token,
    )
    return {"message": "Biometric berhasil didaftarkan"}
@router.post('/login')
def login_biometric(body: BiometricLoginRequest, biometric_service: BiometricServiceInstance):
    member = biometric_service.login_with_biometric(
        device_id=body.device_id,
        biometric_token=body.biometric_token,
    )
    access_token = create_access_token(data={"sub": member.Username})
    return {"access_token": access_token, "token_type":"bearer"}
@router.delete("/revoke")
def revokeb_biometric(biometric_service:BiometricServiceInstance, current_user: Member = Depends(get_current_user_farm)):
    biometric_service.revoke_device(
        username=current_user.Username
    )
    return {"message": "Biometric berhasil dicabut"}
@router.get("/status")
def biometric_status(biometric_service: BiometricServiceInstance, current_user: Member= Depends(get_current_user_farm)):
    is_registered = biometric_service.get_device_status(username=current_user.Username)
    return {"is_registered": is_registered}