from fastapi import APIRouter
from sqlmodel import select, func

from app.database import SessionDB1
from app.model.farm.TempPickTelur import TempPickTelur
from app.model.farm.ayam import Ayam
from app.model.farm.telurpro import Telurpro

router = APIRouter()


@router.get("/layerluar/{date}")
def getlayerluar(session: SessionDB1, date: str):
    telur_hari_ini = session.exec(
        select(Telurpro).where(Telurpro.Tgl == date)
    ).all()

    for item in telur_hari_ini:
        print(item)
    pickup_hari_ini = session.exec(
        select(TempPickTelur).where(TempPickTelur.Tgl == date)
    ).all()

    for item in pickup_hari_ini:
        print(item)
    layerpro = (
        select(
            Ayam.Jenisayam,
            func.coalesce(func.sum(Telurpro.Jmlh), 0).label("jumlah")
        )
        .join(Ayam, Ayam.ID == Telurpro.ID)
        .where(Telurpro.Tgl == date)
        .group_by(Ayam.Jenisayam)
    )
    statement = session.exec(layerpro).all()

    statementtelur = []

    for row in statement:
        statementtelur.append({
            "jenisayam": row[0],
            "jumlah": row[1],
        })

  
    telurpickup = (
        select(
            TempPickTelur.Jenisayam,
            TempPickTelur.Tipe,
            func.coalesce(func.sum(TempPickTelur.Ikat), 0),
            func.coalesce(func.sum(TempPickTelur.Ppn), 0),
            func.coalesce(func.sum(TempPickTelur.Butir), 0),
        )
        .where(TempPickTelur.Tgl == date)
        .group_by(
            TempPickTelur.Jenisayam,
            TempPickTelur.Tipe,
        )
    )

    statementpick = session.exec(telurpickup).all()

    statementpickresult = []

    for row in statementpick:
        statementpickresult.append({
            "jenisayam": row[0],
            "tipe": row[1],
            "ikat": row[2],
            "papan": row[3],
            "butir": row[4],
        })

  
    lastDist = session.exec(
        select(func.max(TempPickTelur.Dist))
        .where(TempPickTelur.Tgl == date)
    ).one()

    print("LAST DIST :", lastDist)

    lastpickupresult = []

    if lastDist is not None:

        lastpickup = (
            select(
                TempPickTelur.Jenisayam,
                TempPickTelur.Tipe,
                func.coalesce(func.sum(TempPickTelur.Ikat), 0),
                func.coalesce(func.sum(TempPickTelur.Ppn), 0),
                func.coalesce(func.sum(TempPickTelur.Butir), 0),
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

        print("LAST PICKUP :", statementlast)

        for row in statementlast:

            ikat = row[2]
            papan = row[3]
            butir = row[4]

            papan += butir // 30
            butir %= 30

            ikat += papan // 10
            papan %= 10

            lastpickupresult.append({
                "trip": lastDist,
                "jenisayam": row[0],
                "tipe": row[1],
                "ikat": ikat,
                "papan": papan,
                "butir": butir,
            })

    return {
        "total_pro": statementtelur,
        "total_pickup": statementpickresult,
        "last_pickup": lastpickupresult,
    }
def getupdatehariini(session: SessionDB1, date:str):
    updatehariini = select(TempPickTelur).where(TempPickTelur.Tgl == date)
    result = session.exec(result).all()