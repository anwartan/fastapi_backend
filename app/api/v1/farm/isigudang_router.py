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
def isigudang(
session: SessionDB1,
date: str,
current_user=Depends(get_current_user_farm),
):
    
    date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    yesterday = date_obj - timedelta(days=1)


    # ==========================================
    # 1. Ambil jumlah telur masuk per jenis ayam
    # ==========================================
    temp_statement = (
        select(
            TempPickTelur.Jenisayam,
            func.coalesce(
                func.sum(
                    (TempPickTelur.Ikat * 360)
                    + (TempPickTelur.Ppn * 30)
                    + TempPickTelur.Butir
                ),
                0,
            ).label("jumlahtelur"),
        )
        .where(TempPickTelur.Tgl == date_obj)
        .group_by(TempPickTelur.Jenisayam)
    )

    result_temp = session.exec(temp_statement).all()

    total_layer_masuk = 0
    total_arab_masuk = 0

    for row in result_temp:
        jenisayam = str(row[0]).strip().lower()
        jumlah = int(row[1] or 0)

        if jenisayam == "layer":
            total_layer_masuk += jumlah
        elif jenisayam == "arab":
            total_arab_masuk += jumlah

    # ==========================================
    # 2. Ambil stok gudang pada tanggal tersebut
    # ==========================================
    telursisa_statement = select(Telursisa).where(
        Telursisa.Tgl == date_obj
    )

    result_telursisa = session.exec(
        telursisa_statement
    ).first()

    # ==========================================
    # 3. Ambil total stok gudang hari sebelumnya
    # ==========================================
    sisa_statement = select(
        func.coalesce(
            func.sum(Telursisa.JmlhLap),
            0,
        )
    ).where(
        Telursisa.Tgl == yesterday
    )

    result_sisamalam = session.exec(
        sisa_statement
    ).first() or 0

    # ==========================================
    # 4. Ambil total telur keluar hari ini
    # ==========================================
    keluar_statement = select(
        func.coalesce(
            func.sum(Telurklr.Jmlh),
            0,
        )
    ).where(
        Telurklr.Tgl == date_obj
    )

    result_keluar = session.exec(
        keluar_statement
    ).first() or 0

    # ==========================================
    # 5. Hitung total stok gudang
    # ==========================================
    if result_telursisa is not None:
        total_gudang = int(
            result_telursisa.JmlhLap or 0
        )
    else:
        total_gudang = max(
            0,
            total_layer_masuk
            + total_arab_masuk
            + int(result_sisamalam)
            - int(result_keluar),
        )

    # ==========================================
    # 6. Kembalikan data Layer dan Arab
    # ==========================================
    return {
        "data": {
            "layer": total_layer_masuk,
            "arab": total_arab_masuk,
            "totalgudang": total_gudang,
        }
    }

