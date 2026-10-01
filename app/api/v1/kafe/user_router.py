import select

from fastapi import APIRouter

from app.database import SessionDBKafeLogin
from app.model.kafe.member import Member


router = APIRouter()
@router.get("/getprofile")
def getpprofile(
    session:SessionDBKafeLogin
):

