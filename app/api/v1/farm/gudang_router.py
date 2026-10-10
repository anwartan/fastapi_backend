import select

from fastapi import APIRouter, Depends

from app.auth import get_current_user_farm
from app.database import SessionDB1
from app.model.farm.telursisa import Telursisa


router = APIRouter
@router.get("/")
def getgudang(session: SessionDB1, date:str, current_user = Depends(get_current_user_farm)):
    gudang_subquery = select(Telursisa).where(Telursisa.Tgl == date)
    result = session.exec(gudang_subquery).first()
    return result
    