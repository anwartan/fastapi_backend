from fastapi import APIRouter, Depends
from sqlmodel import select, func

from app.auth import get_current_user_farm
from app.database import SessionDB1

from app.model.farm.TempPickTelur import TempPickTelur
from app.model.farm.telurklr import Telurklr


router = APIRouter()
def to_butir(ikat, papan, butir):
    return (
        (ikat * 300)
        + (papan * 30)
        + butir
    )
def from_butir(total):
    if total < 0:
        total = 0

    ikat = total // 300
    total = total % 300

    papan = total // 30
    butir = total % 30

    return {
        "ikat": ikat,
        "papan": papan,
        "butir": butir,
    }
@router.get("/layerluar/{date}")
def get_gudang(
    session: SessionDB1,
    date: str,
    current_user=Depends(get_current_user_farm),
):
    telur_masuk = session.exec(
        select(
            TempPickTelur.Jenisayam,
            func.coalesce(
                func.sum(TempPickTelur.Ikat),
                0
            ),
            func.coalesce(
                func.sum(TempPickTelur.Ppn),
                0
            ),
            func.coalesce(
                func.sum(TempPickTelur.Butir),
                0
            ),
        )
        .where(
            TempPickTelur.Tgl <= date
        )
        .group_by(
            TempPickTelur.Jenisayam
        )
    ).all()
    telur_keluar = session.exec(
        select(
            Telurklr.JenisTelur,
            func.coalesce(
                func.sum(Telurklr.Jmlh),
                0
            ),
        )
        .where(
            Telurklr.Tgl <= date
        )
        .group_by(
            Telurklr.JenisTelur
        )
    ).all()
    keluar_dict = {}

    for row in telur_keluar:

        jenisayam = row[0]
        jumlah = row[1] or 0

        keluar_dict[jenisayam] = jumlah
    result = []

    for row in telur_masuk:

        jenisayam = row[0]

        masuk_ikat = row[1] or 0
        masuk_papan = row[2] or 0
        masuk_butir = row[3] or 0

        total_masuk = to_butir(
            masuk_ikat,
            masuk_papan,
            masuk_butir,
        )

        total_keluar = keluar_dict.get(
            jenisayam,
            0
        )
        total_sisa = total_masuk - total_keluar

        if total_sisa < 0:
            total_sisa = 0

        stock = from_butir(total_sisa)

        result.append({
            "jenisayam": jenisayam,

            "ikat": stock["ikat"],
            "papan": stock["papan"],
            "butir": stock["butir"],

            "total_butir": total_sisa,
        })
    return {
        "date": date,
        "stock": result,
    }