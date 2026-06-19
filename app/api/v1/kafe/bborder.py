import select

from fastapi import APIRouter, Depends, HTTPException
from app.auth import get_current_user
from app.database import SessionDBKafe, get_session
from sqlmodel import Session, select,func
from app.model.kafe.bboreder import Bborder
from app.model.kafe.orderstock import Orderstock
from app.model.kafe.belanja import Belanja
from app.request.pengecekaan_request import PengecekaanRequest
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
    if data1:
        data1.Checked = 1
        session.add(data1)
    session.add(data)
    session.commit()
    session.refresh(data)

    return {
        "message": "Berhasil update",
        "data": data
    }

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

@router.get("/{Category}")
def get(session: SessionDBKafe,Category:str,limit: int = 10, offset: int = 0,current_user: dict = Depends(get_current_user)):
    query = select(Bborder).limit(limit).offset(offset).where(Bborder.Category == Category).order_by(Bborder.IDOrder.desc())

    results = session.exec(query).all()
    query_total = select(func.count(Orderstock.IDOrder))
    total = session.exec(query_total).all()
    return {"data": results,
            "paging": {
                "limit": limit,
                "offset": offset,
                "total": total
            }}

@router.get("/{id}/{category}/pengecekaan")
def get_item_by_category_and_id(
    id: int,
    category: str,
    session: SessionDBKafe,
    current_user: dict = Depends(get_current_user)
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
