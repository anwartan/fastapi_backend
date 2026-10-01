from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session_kafe
from app.model.kafe.bboreder import Bborder
from app.model.kafe.belanja import Belanja
from app.model.kafe.jnsstock import Jnsstock
from app.model.kafe.orderstock import Orderstock
from app.model.kafe.Pricedetail import Pricedetail


router = APIRouter()


@router.get("/laporan-per-item")
def laporan_per_item(
    tanggalawal: date,
    tanggalakhir: date,
    jenis: Optional[str] = None,
    session: Session = Depends(get_session_kafe),
):
    if tanggalawal > tanggalakhir:
        raise HTTPException(
            status_code=400,
            detail="Tanggal awal tidak boleh lebih besar dari tanggal akhir"
        )

    if jenis:
        jenis_stock = session.exec(
            select(Jnsstock)
            .where(
                Jnsstock.Jenis == jenis,
                Jnsstock.Aktif == True
            )
        ).first()

        if not jenis_stock:
            raise HTTPException(
                status_code=404,
                detail=f"Jenis '{jenis}' tidak ditemukan"
            )

    data = []

    query_belanja = (
        select(Bborder, Belanja)
        .join(
            Belanja,
            Belanja.ID == Bborder.IDOrder
        )
        .where(
            Bborder.Category == "OB",
            Bborder.Tgl >= tanggalawal,
            Bborder.Tgl <= tanggalakhir,
        )
    )

    if jenis:
        query_belanja = query_belanja.where(
            Belanja.Jenis == jenis
        )

    hasil_belanja = session.exec(query_belanja).all()

    for bborder, belanja in hasil_belanja:
        data.append({
            "Tanggal": bborder.Tgl,
            "Jumlah": belanja.Jmlh,
            "Unit": belanja.Unit,
            "Price": belanja.Price,
            "Inputer": bborder.Inputer,
            "Category": "OB",
            "IDOrder": bborder.IDOrder,
            "Jenis": belanja.Jenis,
        })

    query_orderstock = (
        select(Bborder, Orderstock)
        .join(
            Orderstock,
            Orderstock.IDOrder == Bborder.IDOrder
        )
        .where(
            Bborder.Category == "OS",
            Bborder.Tgl >= tanggalawal,
            Bborder.Tgl <= tanggalakhir,
        )
    )

    if jenis:
        query_orderstock = query_orderstock.where(
            Orderstock.Jenis == jenis
        )
    
    hasil_orderstock = session.exec(query_orderstock).all()

    for bborder, orderstock in hasil_orderstock:
        price_detail = session.exec(
            select(Pricedetail)
            .where(
                Pricedetail.Jenis == orderstock.Jenis,
                Pricedetail.Tgl <= bborder.Tgl,
            )
            .order_by(
                Pricedetail.Tgl.desc(),
                Pricedetail.ID_PriceDetail.desc(),
            )
        ).first()

        price = price_detail.Jmlh if price_detail else None

        data.append({
            "Tanggal": bborder.Tgl,
            "Jumlah": orderstock.Jmlh,
            "Unit": orderstock.unit,
            "Price": price,
            "Inputer": bborder.Inputer,
            "Category": "OS",
            "IDOrder": bborder.IDOrder,
            "Jenis": orderstock.Jenis,
        })

    data.sort(
        key=lambda x: (
            x["Tanggal"],
            x["IDOrder"]
        ),
        reverse=True
    )

    return {
        "tanggalawal": tanggalawal,
        "tanggalakhir": tanggalakhir,
        "jenis": jenis,
        "jumlah": len(data),
        "data": data,
    }