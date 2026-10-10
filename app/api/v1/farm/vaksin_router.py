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
    print("========== DEBUG VAKSIN ==========")
    print("DATE FROM API:", date)

    # STEP 1: Check vaccination data without JOINs
    query_vaksin = select(Ayamvaksin).where(
        Ayamvaksin.Tgl == date
    )

    result_vaksin = session.exec(query_vaksin).all()

    print("VAKSIN COUNT:", len(result_vaksin))
    print("VAKSIN DATA:", result_vaksin)

    # STEP 2: Check the original query with JOINs
    vaksin_umur = (
        select(
            Ayam.Kandang,
            Ayamvaksin.Vaksin,
            Ayamvaksin.Obat,
            Ayamvaksin.KetUmum,
            Ayamvaksin.PerObat,
            Mskanakayam.TglMsk
        )
        .join(
            Ayam,
            Ayam.ID == Ayamvaksin.ID_Bsr
        )
        .join(
            Mskanakayam,
            Mskanakayam.ID == Ayamvaksin.ID_Kcl
        )
        .where(Ayamvaksin.Tgl == date)
    )

    result = session.exec(vaksin_umur).all()

    print("JOIN RESULT COUNT:", len(result))
    print("JOIN RESULT:", result)
    print("==================================")

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

