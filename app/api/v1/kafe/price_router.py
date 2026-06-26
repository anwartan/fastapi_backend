
from datetime import date, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlmodel import select

from app.auth import get_current_user
from app.database import SessionDBKafe, SessionDBKafeLogin
from app.model.kafe.Pricedetail import Pricedetail
from sqlmodel import select

from app.model.kafe.jnsstock import Jnsstock
from app.model.kafe.member import Member
from app.request.price_list_item import PriceListItem


router = APIRouter()
def get_latest_id(session: SessionDBKafe):
    query = select(func.max(Pricedetail.ID_PriceDetail))
    latest_id= session.exec(query).first()
    return latest_id if latest_id is not None else 0



@router.get("/")
def get(
    session: SessionDBKafe,        # db belanja (pricedetail)
    session_gaji: SessionDBKafeLogin,   # db gaji (member)
    search: str = None,
    limit: int = 10,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    # 1. Ambil pricedetail dulu
    query = select(Pricedetail)
    if search:
        query = query.where(Pricedetail.Jenis.like(f"%{search}%"))
    query = query.order_by(Pricedetail.ID_PriceDetail.desc()).offset(offset).limit(limit)
    results = session.exec(query).all()

    # 2. Kumpulkan semua Inputer ID yang unik
    inputer_ids = list({r.Inputer for r in results if r.Inputer})

    # 3. Ambil member dari db gaji sekaligus (1 query, bukan N query)
    member_map = {}
    if inputer_ids:
        members = session_gaji.exec(
            select(Member).where(Member.ID.in_(inputer_ids))
        ).all()
        member_map = {m.ID: m.Nama for m in members}

    # 4. Merge
    data = [
        {
            "ID_PriceDetail": r.ID_PriceDetail,
            "Tgl": r.Tgl,
            "Jenis": r.Jenis,
            "Jmlh": r.Jmlh,
            "Inputer": r.Inputer,
            "NamaInputer": member_map.get(r.Inputer),
        }
        for r in results
    ]

    # 5. Total
    query_total = select(func.count(Pricedetail.ID_PriceDetail))
    if search:
        query_total = query_total.where(Pricedetail.Jenis.like(f"%{search}%"))
    total = session.exec(query_total).first()

    return {
        "data": data,
        "paging": {"limit": limit, "offset": offset, "total": total}
    }
@router.get("/search/{jenis}")
def get_by_jenis(
    jenis: str,
    session: SessionDBKafe,
    session_member: SessionDBKafeLogin,  # ← sesuaikan nama session member kamu
    current_user: dict = Depends(get_current_user)
):
    query = (
        select(Pricedetail)
        .where(Pricedetail.Jenis.like(f"%{jenis}%"))
        .order_by(Pricedetail.ID_PriceDetail.desc())
    )
    results = session.exec(query).all()

    # Ambil nama member
    inputer_ids = list({r.Inputer for r in results if r.Inputer})
    member_map = {}
    if inputer_ids:
        members = session_member.exec(
            select(Member).where(Member.ID.in_(inputer_ids))
        ).all()
        member_map = {m.ID: m.Nama for m in members}

    data = [
        {
            "ID_PriceDetail": r.ID_PriceDetail,
            "Tgl": r.Tgl,
            "Jenis": r.Jenis,
            "Jmlh": r.Jmlh,
            "Inputer": r.Inputer,
            "NamaInputer": member_map.get(r.Inputer),
        }
        for r in results
    ]

    return {"data": data}
@router.get("/date/{tanggal}")
def get_by_date(
    session: SessionDBKafe,
    tanggal: date,
    current_user: dict = Depends(get_current_user)
):
    query = select(Pricedetail).where(Pricedetail.Tgl == tanggal)
    results = session.exec(query).all()
    return {"data": results}
@router.post("/create")
def create(
    session: SessionDBKafe,
    order: PriceListItem,
    current_user: Member = Depends(get_current_user),
):
    new_id = get_latest_id(session) + 1

    price = Pricedetail(
        ID_PriceDetail=new_id,
        Tgl=datetime.strptime(order.tgl, "%Y-%m-%d").date(),
        Jenis=order.jenis,
        Jmlh=order.Jmlh,
        Inputer=current_user.ID,
    )

    session.add(price)
    session.commit()
    session.refresh(price)

    return {
        "data": price
    }
