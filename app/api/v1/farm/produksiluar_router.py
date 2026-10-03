from fastapi import APIRouter
from sqlmodel import select, func

from app.database import SessionDB1
from app.model.farm.TempPickTelur import TempPickTelur
from app.model.farm.ayam import Ayam
from app.model.farm.telurklr import Telurklr
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
                func.coalesce(func.sum(TempPickTelur.Ikat), 0),
                func.coalesce(func.sum(TempPickTelur.Ppn), 0),
                func.coalesce(func.sum(TempPickTelur.Butir), 0),
            )
            .where(
                TempPickTelur.Tgl == date,
            )
            .group_by(
                TempPickTelur.Jenisayam,
            )
        )

        keluar = (
            select(
              func.coalesce(func.sum(Telurklr.Jmlh),0),Telurklr.JenisTelur
            ).where(Telurklr.Tgl == date).group_by(Telurklr.JenisTelur)
        )
        ambillast = session.exec(keluar).all()
        statementlast = session.exec(lastpickup).all()
        for msk in statementlast:
            jenisayam = msk[0]
            masukikat = int(msk[1])
            masukppn = int(msk[2])
            masukbtr = int(msk[3])
            totalmasuk = (
                (masukikat * 300)
                + (masukppn * 30)
                + masukbtr
            )
            for klr in ambillast:
                jenisklr = klr[1]
                jmlhklr = klr[0]
                if(jenisklr == jenisayam):
                    totalsisa = totalmasuk - jmlhklr
                    if(totalsisa < 0):
                        totalsisa = 0
                    
                    
                    lastpickupresult.append({
                        "jenisayam": row[0],
                        "ikat": totalsisa//300,
                        "papan": (totalsisa%300 )//30,
                        "butir": (totalsisa%300 )%30,
                    })
                    break

    return {
        "total_pro": statementtelur,
        "total_pickup": statementpickresult,
        "last_pickup": lastpickupresult,
    }
def getupdatehariini(session: SessionDB1, date:str):
    updatehariini = select(TempPickTelur).where(TempPickTelur.Tgl == date)
    result = session.exec(result).all()