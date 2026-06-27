from re import A
from unittest import result

from fastapi import APIRouter


from app.database import SessionDB1
from app.model.farm.TempPickTelur import TempPickTelur
from app.model.farm.TempPickupTelur import TempPickUpTelur
from app.model.farm.ayam import Ayam
from app.model.farm.telurpro import Telurpro
from sqlmodel import select, func

router = APIRouter()
@router.get("/layerluar/{date}")
def getlayerluar(session:SessionDB1, date: str):
    layerpro = select(Ayam.Jenisayam ,func.sum(Telurpro.Jmlh)).join(Ayam, Ayam.ID == Telurpro.ID).where(Telurpro.Tgl == date).group_by(Ayam.Jenisayam)
    statement = session.exec(layerpro).all()

    telurpickup = (
        select(
            TempPickTelur.Jenisayam,
            TempPickTelur.Tipe,
            func.sum(TempPickTelur.Ikat),
            func.sum(TempPickTelur.Ppn),
            func.sum(TempPickTelur.Butir)
        )
        .where(TempPickTelur.Tgl == date)
        .group_by(TempPickTelur.Jenisayam, TempPickTelur.Tipe)
    )

    statementpick = session.exec(telurpickup).all()

    statementpickresult = [];
    for i in statementpick:
        statementpickresult.append({
            "jenisayam": i[0],
            "tipe": i[1],
            "ikat": i[2],
            "papan": i[3],
            "butir": i[4],
        })
    statementtelur = [];
    for jenis , jumlah in statement:
        statementtelur.append({
            "jenisayam": jenis,
            "jumlah": jumlah
        })
    return {
        "total_pro":statementtelur,
        "total_pickup": statementpickresult,  
    }