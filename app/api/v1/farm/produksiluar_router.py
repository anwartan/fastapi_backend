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
    lastDist = session.exec(
    select(func.max(TempPickTelur.Dist))
    .where(TempPickTelur.Tgl == date)
    ).one()
    lastpickup = (
    select(
        TempPickTelur.Jenisayam,
        TempPickTelur.Tipe,
        func.sum(TempPickTelur.Ikat),
        func.sum(TempPickTelur.Ppn),
        func.sum(TempPickTelur.Butir),
    )
    .where(
        TempPickTelur.Tgl == date,
        TempPickTelur.Dist == lastDist,
    )
    .group_by(
        TempPickTelur.Jenisayam,
        TempPickTelur.Tipe,
    )
)
    statementlast = session.exec(lastpickup).all()
    lastpickupresult = []
    for i in statementlast:
        ikat = i[2] or 0
        papan = i[3] or 0
        butir = i[4] or 0

        # 30 butir = 1 papan
        papan += butir // 30
        butir %= 30

        # 10 papan = 1 ikat
        ikat += papan // 10
        papan %= 10
    lastpickupresult.append({
        "trip": lastDist,
        "jenisayam": i[0],
        "tipe": i[1],
        "ikat": ikat,
        "papan": papan,
        "butir": butir,
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
        "last_pickup": lastpickupresult,  
    }