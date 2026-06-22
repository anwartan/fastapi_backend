
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlmodel import select

from app.auth import get_current_user
from app.database import SessionDBKafe
from app.model.kafe.Pricedetail import Pricedetail


router = APIRouter()
@router.get("/")
def get(
    session: SessionDBKafe,
    search: str = None,
    limit: int = 10,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    query = select(Pricedetail)

    if search:
        query = query.where(Pricedetail.Jenis.like(f"%{search}%"))

    # 🔥 ORDER BY DESC (terbaru dulu)
    query = query.order_by(Pricedetail.ID_PriceDetail.desc())

    query = query.offset(offset).limit(limit)

    results = session.exec(query).all()

    query_total = select(func.count(Pricedetail.ID_PriceDetail))

    if search:
        query_total = query_total.where(
            Pricedetail.Jenis.like(f"%{search}%")
        )

    total = session.exec(query_total).first()

    return {
        "data": results,
        "paging": {
            "limit": limit,
            "offset": offset,
            "total": total
        }
    }
from sqlmodel import select

@router.get("/search/{jenis}")
def get_by_jenis(
    jenis: str,
    session: SessionDBKafe,
    current_user: dict = Depends(get_current_user)
):
    query = (
        select(Pricedetail)
        .where(Pricedetail.Jenis.like(f"%{jenis}%"))
        .order_by(Pricedetail.ID_PriceDetail.desc())
    )

    results = session.exec(query).all()

    return {"data": results}
@router.get("/date/{tanggal}")
def get_by_date(
    session: SessionDBKafe,
    tanggal: date,
    current_user: dict = Depends(get_current_user)
):
    query = select(Pricedetail).where(Pricedetail.Tgl == tanggal)
    results = session.exec(query).all()
    return {"data": results}
