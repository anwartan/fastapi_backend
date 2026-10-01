from dataclasses import field

from pydantic import BaseModel, field_validator

from app.api.v1.farm import biometric_router


class BiometricRegisterRequest(BaseModel):
    device_id: str
    biometric_token: str
    @field_validator("device_id","biometric_token")
    def must_not_be_empty(cls, y:str) -> str:
        if not y or not y.strip():
            raise ValueError("Field tidak boleh kosong")
        return y.strip()
    
    
class BiometricLoginRequest(BaseModel):
    device_id: str
    biometric_token: str
    @field_validator("device_id", "biometric_token")
    def must_not_be_empty(cls, y:str) -> str:
            if not y or not y.strip():
                raise ValueError("Field tidak boleh kosong")
            return y.strip()
        
class BiometricRevokeRequest(BaseModel):
    device_id: str
            