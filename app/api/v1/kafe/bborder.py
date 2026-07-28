from datetime import date
import select

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Subquery
from app.auth import get_current_user
from app.database import SessionDBKafe, SessionDBKafeLogin, get_session
from sqlmodel import Session, select,func
from app.model.kafe import bboreder
from app.model.kafe.bboreder import Bborder
from app.model.kafe.member import Member
from app.model.kafe.orderstock import Orderstock
from app.model.kafe.belanja import Belanja
from app.request.pengecekaan_request import PengecekaanRequest
from app.request.updatepengecekaanrequest import UpdatePengecekaan
router = APIRouter()

    
@router.get("/getall")
def get_all(
    session: SessionDBKafe,
    current_user: dict = Depends(get_current_user)
):
 
    query = (
        select(Bborder)
        .where(Bborder.Checked == 0)
        .order_by(Bborder.IDOrder.desc())
    )

    results = session.exec(query).all()

    return {
        "data": results
    }   
@router.get("/getallchecked")
def get_all_checked(
    session: SessionDBKafe,
    current_user: Member = Depends(get_current_user)
):
 
    query = (
        select(Bborder)
        .where(Bborder.Checked == 1)
        .order_by(Bborder.IDOrder.desc())
    )

    results = session.exec(query).all()

    return {
        "data": results
    }  
@router.get("/")
def get_bborder(session: Session = Depends(get_session),current_user: dict = Depends(get_current_user)):
    try:
        subquery = (
            select(func.count(Orderstock.IDOrder))
            .where(Orderstock.IDOrder == Bborder.IDOrder)
            .correlate(Bborder)
            .scalar_subquery()
        )

        query = select(
                Bborder,
                func.coalesce(subquery, 0).label("total_items")
            ).where(Bborder.Checked==False).limit(100).order_by(Bborder.IDOrder.desc())

        

        results = session.exec(query).all()

        data = []
        for bborder, total in results:
            item = bborder.dict()    
            item["total_items"] = total
            data.append(item)

        return  {"data": data,
                "paging": {
                 "total": total
             }}

    except Exception as e:
        return {"error": str(e)}    

@router.put("/pengecekaan")
def pengecekaan(
    req: PengecekaanRequest,
    session: SessionDBKafe,
   # current_user: dict = Depends(get_current_user)
):

    if req.category == "OB":
        query = select(Belanja).where(
            Belanja.ID == req.id,
            Belanja.Jenis == req.jenis
        )
    else:
        query = select(Orderstock).where(
            Orderstock.IDOrder == req.id,
            Orderstock.Jenis == req.jenis
        )
    

    data = session.exec(query).first()
    data1=session.exec(
        select(Bborder).where(Bborder.IDOrder==req.id)
    ).first()
    print(data)

    if data is None:
        raise HTTPException(
            status_code=404,
            detail="Data tidak ditemukan"
        )

  
    data.Checked = 1  
    
    data1.Checked = 1
    data1.Total=req.total
    session.add(data1)
    session.add(data)
    session.commit()
    session.refresh(data)

    return {
        "message": "Berhasil update",
        "data": data
    }

@router.get("/{tanggal}/tanggal/checked")
def get_bborder_by_tanggal(
    tanggal: date,
    session: SessionDBKafe,
    current_user: dict = Depends(get_current_user)
):
    query = (
        select(Bborder)
        .where(Bborder.Tgl == tanggal)
        .where(Bborder.Checked == 1)
        .order_by(Bborder.IDOrder.desc())
    )

    return {"data": session.exec(query).all()}

@router.get("/{Category}/{Tanggal}")
def GetBYCategoryAndTanggal(session:SessionDBKafe, Category:str,Tanggal:str,current_user: dict = Depends(get_current_user)):
    
    query = select(Bborder).where(Bborder.Category   == Category, Bborder.Tgl == Tanggal)
    results = session.exec(query).first()
    if not results:
        latest_query = select(func.max(Bborder.IDOrder))
        latest_result = session.exec(latest_query).first()
        if latest_result is  None:
            current_id = 1
        else:
            current_id = latest_result + 1
        new_bborder = Bborder(IDOrder=current_id, Category=Category, Tgl=Tanggal, Total=0, Aktif=True, Inputer=0, Checked=False, ID_Check=0, Ket="")
        session.add(new_bborder)
        session.commit()
        querysearch = select(Bborder).where(Bborder.IDOrder == latest_result)
        results = session.exec(querysearch).first()
        return {"message": "Data tidak ditemukan"}
    return {"data": results}

@router.get("/category/filter/{category}")
def filterbycategory(
    session:SessionDBKafe,
    category:str,
    current_user: Member = Depends(get_current_user)
):
    query=select(Bborder).where(Bborder.Category==category)
    subquery=session.exec(query).all()
    return {
        "data": subquery
    }
@router.get("/{Category}")
def get(
    session: SessionDBKafe,
    session_login: SessionDBKafeLogin,
    Category: str,
    limit: int = 30,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
):
    if Category.upper() == "OS":
        query = (
            select(Bborder, Orderstock.IDOrder)
            .join(Orderstock, Orderstock.IDOrder == Bborder.IDOrder)   
            .distinct(Bborder.IDOrder)            
            .where(
                Bborder.Category == Category,
                Bborder.Checked == 0,
            )
            .order_by(Bborder.IDOrder.desc())
            .limit(limit)
            .offset(offset)
        )
    else:
        query = (
            select(Bborder, Belanja.ID)
            .join(Belanja, Belanja.ID == Bborder.IDOrder)   
            .distinct(Bborder.IDOrder)
         
            .where(
                Bborder.Category == Category,
                Bborder.Checked == 0,
            )
            .order_by(Bborder.IDOrder.desc())
            .limit(limit)
            .offset(offset)
        )

    results = session.exec(query).all()

    # Ambil semua ID Inputer
    inputer_ids = list({bb.Inputer for bb, _ in results if bb.Inputer})

    # Ambil Username dari database Login
    member_map = {}
    if inputer_ids:
        members = session_login.exec(
            select(Member).where(Member.ID.in_(inputer_ids))
        ).all()

        member_map = {
            member.ID: member.Username
            for member in members
        }

    data = []
    for bb, divisi in results:
        item = bb.model_dump()
        item["Divisi"] = divisi
        item["Inputer"] = member_map.get(bb.Inputer, str(bb.Inputer))
        data.append(item)

    total = session.exec(
        select(func.count(Bborder.IDOrder)).where(
            Bborder.Category == Category,
            Bborder.Checked == 0,
        )
    ).one()

    return {
        "data": data,
        "paging": {
            "limit": limit,
            "offset": offset,
            "total": total,
        },
    }
@router.get("/{category}/{divisi}/divisi")
def get_bborder(
    session: SessionDBKafe,
    session_login: SessionDBKafeLogin,
    category: str,
    divisi: str,
    limit: int = 30,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
):
    if category.upper() == "OS":
        query = (
            select(Bborder, Orderstock.Divisi)
            .join(Orderstock, Orderstock.IDOrder == Bborder.IDOrder)
            .where(
                Bborder.Category == category,
                Orderstock.Divisi == divisi,
                Bborder.Checked == 0,
            )
            .distinct()
            .order_by(Bborder.IDOrder.desc())
            .limit(limit)
            .offset(offset)
        )
    else:
        query = (
            select(Bborder, Belanja.Divisi)
            .join(Belanja, Belanja.ID == Bborder.IDOrder)
            .where(
                Bborder.Category == category,
                Belanja.Divisi == divisi,
                Bborder.Checked == 0,
            )
            .distinct()
            .order_by(Bborder.IDOrder.desc())
            .limit(limit)
            .offset(offset)
        )

    results = session.exec(query).all()

    # Ambil semua ID Inputer
    inputer_ids = list({bb.Inputer for bb, _ in results if bb.Inputer})

    # Ambil Username dari database Login
    member_map = {}
    if inputer_ids:
        members = session_login.exec(
            select(Member).where(Member.ID.in_(inputer_ids))
        ).all()

        member_map = {
            member.ID: member.Username   # ganti menjadi member.Nama jika ingin nama
            for member in members
        }

    data = []

    for bb, divisi_db in results:
        item = bb.model_dump()
        item["Divisi"] = divisi_db
        item["Inputer"] = member_map.get(bb.Inputer, str(bb.Inputer))
        data.append(item)

    return {
        "data": data,
        "paging": {
            "limit": limit,
            "offset": offset,
            "total": len(data)
        }
    }
@router.get("/{id}/{category}/pengecekaan")
def get_item_by_category_and_id(
    id: int,
    category: str,
    session: SessionDBKafe,
    current_user: Member = Depends(get_current_user)
):
    if category == "OB":
        query = select(Belanja).where(
            Belanja.ID == id,
            Belanja.Checked != 1
        )
    elif category == "OS":
        query = select(Orderstock).where(
            Orderstock.IDOrder == id,
            Orderstock.Checked != 1
        )
    else:
        return {"data": []}

    total = session.exec(query).all()
    return {"data": total}


@router.get("/RecapanPengecekaan/recap/{id}/{category}")
def get_item_recap_by_category_and_id(
    id: int,
    category: str,
    session: SessionDBKafe,
    current_user: Member = Depends(get_current_user)
):
    if category == "OB":
        data = session.exec(
            select(Belanja).where(
                Belanja.ID == id,
                Belanja.Checked == 0
            )
        ).all()

    elif category == "OS":
        data = session.exec(
            select(Orderstock).where(
                Orderstock.IDOrder == id,
                Orderstock.Checked == 0
            )
        ).all()

    else:
        return {
            "total": 0,
            "data": []
        }

    bborder = session.exec(
        select(Bborder).where(Bborder.IDOrder == id)
    ).first()

    return {
        "total": bborder.Total if bborder else 0,
        "data": data
    }
@router.put("/updatepengecekaan")
def updatepengecekaan(
    session: SessionDBKafe,
    request: UpdatePengecekaan,
    current_user: Member = Depends(get_current_user)
):
    belanja = session.exec(
        select(Belanja).where(
            Belanja.ID == request.id,
            Belanja.Jenis == request.jenis
        )
    ).first()

    if belanja is None:
        raise HTTPException(
            status_code=404,
            detail="Data tidak ditemukan"
        )

    belanja.JmlhPenerima = request.jmlhpenerimaan
    belanja.Jmlh = request.jmlh

    session.add(belanja)
    session.commit()
    session.refresh(belanja)

    return {
        "message": "Berhasil update",
        "data": belanja
    }