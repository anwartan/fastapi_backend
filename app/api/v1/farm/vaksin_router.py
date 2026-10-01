from fastapi import APIRouter, Depends
from requests import session
from sqlmodel import select

from app.auth import get_current_user_farm
from app.database import SessionDB1
from sqlmodel import select

from app.model.farm.ayam import Ayam
from app.model.farm.ayamvaksin import Ayamvaksin
from app.model.farm.mskanakayam import Mskanakayam


router = APIRouter()
@router.get("/vaksin/{date}")
def getvaksin(session: SessionDB1, date:str, current_user = Depends(get_current_user_farm)):
    vaksin_umur = select(Ayam.Kandang, Ayamvaksin.Vaksin, Ayamvaksin.Obat, Ayamvaksin.KetUmum, Ayamvaksin.PerObat, Mskanakayam.TglMsk
                           ).join(
                                Ayam,Ayam.ID == Ayamvaksin.ID_Bsr
                           ).join(Mskanakayam, Mskanakayam.ID == Ayamvaksin.ID_Kcl).where(Ayamvaksin.Tgl == date
                        )
    result = session.exec(vaksin_umur).all()
    
    return {
        "data": [
            {
                "Kandang": row.Kandang,
                "Vaksin": row.Vaksin,
                "Obat": row.Obat,
                "KetUmum": row.KetUmum,
                "PerObat": row.PerObat,
                "TglMsk": row.TglMsk
            }
            for row in result
        ]
    }