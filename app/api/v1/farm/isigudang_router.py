from datetime import datetime, timedelta


from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlmodel import select


from app.auth import get_current_user_farm
from app.database import SessionDB1
from app.model.farm.TempPickTelur import TempPickTelur
from app.model.farm.telurklr import Telurklr
from app.model.farm.telursisa import Telursisa


router = APIRouter()


@router.get("/gudangisi/{date}")
def isigudang(session: SessionDB1, date: str, current_user = Depends(get_current_user_farm)):

    telursisa_statemeny = select(Telursisa).where(
        Telursisa.Tgl == date 
    )

    result_telursisa = session.exec(
        telursisa_statemeny
    ).first()

    date_obj = datetime.strptime(
        date,
        "%Y-%m-%d"
    ).date()
    yesterday = date_obj - timedelta(days=1)
    if result_telursisa is None:
        temppicktelur_state = select(
            func.coalesce(
                func.sum(
                    (TempPickTelur.Ikat * 360)
                    + (TempPickTelur.Ppn * 30)
                    + TempPickTelur.Butir
                ),
                0
            )
        ).where(
            TempPickTelur.Tgl == date_obj
        ).group_by(TempPickTelur.Tipe)

        result_temp = session.exec(
            temppicktelur_state
        ).first()

        sisasemalam_state = select(
            func.coalesce(
                Telursisa.JmlhLap,
                0
            )
        ).where(
            Telursisa.Tgl == yesterday
        )

        result_sisamalam = session.exec(
            sisasemalam_state
        ).first()

        keluar_state = select(
            func.coalesce(
                func.sum(Telurklr.Jmlh),
                0
            )
        ).where(
            Telurklr.Tgl == date_obj
        )

        result_keluar = session.exec(
            keluar_state
        ).first()
        tipe_statement = select(TempPickTelur).where(TempPickTelur.Tipe == "Layer" & TempPickTelur.Tipe == "Arab")
        result_tipe = session.exec(tipe_statement).first()
        print("hai", result_temp)
        print("halo", result_sisamalam)
        print("hi", result_keluar)

        return {
            "data": {
                "jumlahtelur": (
                    result_temp
                    + result_sisamalam
                    - result_keluar
                )
            }
        }

    else:

        return {
            "data": {
                "jumlahtelur": result_telursisa.JmlhLap
            }
        }