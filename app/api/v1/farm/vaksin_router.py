from fastapi import APIRouter, Depends
from sqlmodel import select

from app.auth import get_current_user_farm
from app.database import SessionDB1

from app.model.farm.ayam import Ayam
from app.model.farm.ayamvaksin import Ayamvaksin
from app.model.farm.mskanakayam import Mskanakayam


router = APIRouter()


@router.get("/vaksin/{date}")
def getvaksin(
    session: SessionDB1,
    date: str,
    current_user=Depends(get_current_user_farm)
):
    vaksin_umur = (
        select(
            Ayam.Kandang,
            Ayamvaksin.Vaksin,
            Ayamvaksin.PerVaksin,
            Ayamvaksin.Obat,
            Ayamvaksin.PerObat,
            Ayamvaksin.KetUmum,
            Mskanakayam.TglMsk
        )
        .select_from(Ayamvaksin)
        .join(
            Ayam,
            Ayam.ID == Ayamvaksin.ID_Bsr,
            isouter=True
        )
        .join(
            Mskanakayam,
            Mskanakayam.ID == Ayamvaksin.ID_Kcl,
            isouter=True
        )
        .where(Ayamvaksin.Tgl == date)
    )
    result = session.exec(vaksin_umur).all()

    return {
        "data": [
            {
                "Kandang": row.Kandang,
                "Vaksin": row.Vaksin,
                "PerVaksin":row.PerVaksin,
                "Obat": row.Obat,
                "PerObat": row.PerObat,
                "KetUmum": row.KetUmum,
                "TglMsk": row.TglMsk
            }
            for row in result
        ]
    }
    
