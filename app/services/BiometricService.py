
from datetime import datetime
import hashlib
import secrets
import token
from typing import Annotated

from aiosmtplib import status
from certifi import where
from fastapi import Depends, HTTPException,status



from app.database import SessionDBKafeLogin
from app.model.kafe.member import Member
from sqlmodel import select

def _hash_token(token:str)->str:
    return hashlib.sha256(token.encode()).hexdigest()
class BiometricService:
    def __init__(self,session:SessionDBKafeLogin):
        self.session=session
    def register_device(self,username:str,device_id:str,biometric_token:str) -> Member:
        token_hash=_hash_token(biometric_token)
        existing=self.session.exec(
            select(Member).where(
                Member.Username==username,
            )
        ).first()
        if existing:
            existing.TokenBiometric=token_hash
            existing.Device_id = device_id
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing
        raise Exception("Member Not found")
    

    def login_with_biometric(self,device_id:str,token_biometric:str)->Member:
        hast_token = _hash_token(token_biometric)
        existing=self.session.exec(
            select(Member).where(Member.Device_id==device_id)
        ).first()
        if not existing: 
            raise HTTPException(
                status_code=status.HTTP_401_NOT_FOUND,
                detail="user tidak ditemukan",)
        if not secrets.compare_digest(existing.TokenBiometric or "",hast_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token Biometric tidak valid"
            )
        return existing
    def revoke_device(self,username:str):
        existing=self.session.exec(
            select(Member).where(Member.Username==username)
        ).first()
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Device Not Found'
            )
        existing.TokenBiometric=None
        existing.Device_id=None
        self.session.add(existing)
        self.session.commit()
    def get_device_status(self,username:str)->bool:
        existing=self.session.exec(
            select(Member).where(Member.Username==username)
        ).first()
        return existing is not None and existing.Device_id is not None and existing.TokenBiometric is not None
        

def get_biometric_service(session:SessionDBKafeLogin, ) -> BiometricService:
    return BiometricService(session)
    
BiometricServiceInstance = Annotated[BiometricService, Depends(get_biometric_service)]