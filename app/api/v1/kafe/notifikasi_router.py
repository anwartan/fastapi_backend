

from fastapi import APIRouter, Depends
from requests import session

from app.auth import get_current_user
from app.database import SessionDBKafeLogin
from app.model.kafe.member import Member
from app.request.notifikasiRequest import NotifikasiRequuest


router = APIRouter()
@router.put("/")
def notification(
    session:SessionDBKafeLogin,
    req:NotifikasiRequuest,
    current_user: Member = Depends(get_current_user)
    ):
    current_user.TokenNotifikasi=req.token_notifikasi
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return {
        "message": "Berhasil update",
    }
