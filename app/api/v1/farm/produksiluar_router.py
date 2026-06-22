from fastapi import APIRouter

from app.database import SessionDB1
from app.model.farm.telurpro import Telurpro
from sqlmodel import select

router = APIRouter()
@router.get("/layerluar/{date}")
def getlayerluar(session:SessionDB1, date: str):
    layerpro = select(Telurpro.Jmlh).where(Telurpro.Tgl == date)
    statement = session.exec(layerpro).first()
    return statement