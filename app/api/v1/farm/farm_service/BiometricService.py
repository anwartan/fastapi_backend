import hashlib
import secrets
import select
from typing import Annotated


from aiosmtplib import status
from fastapi import Depends, HTTPException

from sqlmodel import select
from app.database import SessionDB1

from app.model.farm.login import Login



def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class BiometricService:
    def __init__(self, session: SessionDB1):
        self.session = session
    def register_device(self, username: str, device_id: str, biometric_token: str)->Login:
        token_hash = _hash_token(biometric_token)
        existing = self.session.exec(select(Login).where(Login.Username == username)).first()
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")
        existing.DeviceId = device_id
        existing.TokenBiometric=token_hash
        self.session.add(existing)
        self.session.commit()
        self.session.refresh(existing)
        return existing
    def login_with_biometric(self, device_id: str, biometric_token: str) -> Login:
        token_hash = _hash_token(biometric_token)
        member = self.session.exec(select(Login).where(Login.DeviceId == device_id)).first()
        if not member:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Device tidak terdaftar")
        if not secrets.compare_digest(member.TokenBiometric or "", token_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token biometric tidak valid")
        return member
    def revoke_device(self, username:str) -> None:
        member = self.session.exec(select(Login).where(Login.Username == username)).first()
        if not member: 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device tidak ditemukan")
        member.DeviceId = None
        member.TokenBiometric = None
        self.session.add(member)
        self.session.commit()
        
    def get_device_status(self, username: str) -> bool:
        member = self.session.exec(select(Login).where(Login.Username == username)).first()
        return bool(member and member.DeviceId and member.TokenBiometric)
    
    
def get_biometric_service(session: SessionDB1) -> BiometricService:
    return BiometricService(session)
BiometricServiceInstance = Annotated[BiometricService, Depends(get_biometric_service)]
        