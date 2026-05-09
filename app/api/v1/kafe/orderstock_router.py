import select
from unittest import result

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import JSONResponse
import app
from app.api.v1.kafe import bborder
from app.database import SessionDB1
from sqlmodel import Date, select,func

from app.model.kafe.bboreder import Bborder
from app.model.kafe.jnsstock import Jnsstock
from app.model.kafe.orderstock import Orderstock
from app.request.createOrderRequestJenisStock import CreateOrderStockRequest
from datetime import datetime 
from app.model.kafe.belanja import Belanja
router = APIRouter()

    
@router.get("/")
def get(session: SessionDB1, limit: int = 10, offset: int = 0):
    query = select(Orderstock).limit(limit).offset(offset)
    results = session.exec(query).all()
    query_total = select(func.count(Orderstock.IDOrder))
    total = session.exec(query_total).first()
    return {"data": results,
            "paging": {
                "limit": limit,
                "offset": offset,
                "total": total
            }}
@router.get("/{id}")
def get_by_id(id:int,session: SessionDB1):
    query = select(Orderstock).where(Orderstock.IDOrder == id)
    result = session.exec(query).all()
    if result is None:
        return JSONResponse(content={"message": "belanja not found"}, status_code=404)
    else:       
        return {"data": result}
    

    return {"data": result} 
@router.get("/{category}/{Tanggal}")
def GetBYCategory(category: str, Tanggal: str, session: SessionDB1):
    query = select(Orderstock).where(Orderstock.Category == category, Orderstock.Tanggal == Tanggal)
    result = session.exec(query).all()
    return {"data": result}
def get_latest_id(session: SessionDB1):
    query = select(func.max(Bborder.IDOrder))
    latest_id= session.exec(query).first()
    return latest_id if latest_id is not None else 0


@router.post("/create")
def create(session: SessionDB1, order:CreateOrderStockRequest):
    new_id = get_latest_id(session) + 1
    date=datetime.strptime(order.tgl, "%Y-%m-%d").date()    
    new_order = Bborder(
        IDOrder=new_id,
        Tgl=date,
        Total=0,
        Aktif=True,
        Inputer="",
        Category=order.category,
        Checked=False,
        ID_Check=0,
        Ket=order.ket


    )
    session.add(new_order)
    for item in order.items:
        jenis_db = session.exec(
            select(Jnsstock).where(Jnsstock.Jenis == item.jenis_stock)
        ).first()

        if not jenis_db:
            raise HTTPException(
                status_code=400,
                detail=f"Jenis stock '{item.jenis_stock}' tidak ditemukan"
            )
    for item in order.items:
        order_stock = Orderstock(
            Tgl=date,
            IDOrder=new_id,
            Jenis=item.jenis_stock,
            Jmlh=item.qty,
            JmlhInp=0,
            unit=jenis_db.Unit,
            Divisi="",
            Inputer=0,
            Ket=item.keterangan_jenis_stock         )
        session.add(order_stock)
    session.commit()
    session.refresh(new_order)
    return{
        "data":new_order 
    }
@router.delete("/{id}/{jenis}")
def delete(id: int,jenis: str, session: SessionDB1):
    query = select(Orderstock).where(Orderstock.IDOrder == id, Orderstock.Jenis == jenis)
    result = session.exec(query).first()
    if not result:
        raise HTTPException(status_code=404, detail="order stock not found")
    session.delete(result)
    session.commit()
    return {"message": "order stock deleted successfully"}
