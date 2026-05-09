import select

from fastapi import APIRouter, HTTPException
from app.database import SessionDB1, get_session
from sqlmodel import select,func
from app.model.kafe.belanja import Belanja
from app.model.kafe.bboreder import Bborder
from app.model.kafe.jnsstock import Jnsstock
from app.request import belanja_item_request
from app.request.create_order_request import CreateOrderRequest
from datetime import datetime 
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

router = APIRouter()
def get_latest_id(session: SessionDB1):
    query = select(func.max(Bborder.IDOrder))
    latest_id= session.exec(query).first()
    return latest_id if latest_id is not None else 0


@router.get("/")
def get(session: SessionDB1, limit: int = 10, offset: int = 0):
    query = select(Belanja).limit(limit).offset(offset)
    results = session.exec(query).all()
    query_total = select(func.count(Belanja.ID))
    total = session.exec(query_total).all()
    return {"data": results,
            "paging": {
                "limit": limit,
                "offset": offset,
                "total": total
            }}
@router.get("/{id}")
def get_by_id(id:int,session: SessionDB1):
    
    query = select(Belanja).where(Belanja.ID == id)

    result = session.exec(query).all()
    
    if not result:
        return JSONResponse(content={"message": "belanja not found"}, status_code=404)
    else:
        return {"data": result}
    
@router.delete("/{id}/{jenis}")
def delete(id: int,jenis: str, session: SessionDB1):
    print("id",id)
    print("jenis",jenis)
    query = select(Belanja).where(Belanja.ID == id, Belanja.Jenis == jenis)
    result = session.exec(query).first()
    print("qsdcxs",result)
    if not result:
        raise HTTPException(status_code=404, detail="belanja not found")
    session.delete(result)
    session.commit()
    return {"message": "belanja deleted successfully"}

@router.post("/create")
def create(session: SessionDB1, order:CreateOrderRequest):

    new_id = get_latest_id(session) + 1
    date=datetime.strptime(order.tgl, "%Y-%m-%d")
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
    # jenis_stock_collected = [item.jenis_stock for item in order.items]
    for item in order.items:
        jenis_db = session.exec(
            select(Jnsstock).where(Jnsstock.Jenis == item.jenis_stock)
        ).first()

        if not jenis_db:
            raise HTTPException(
                status_code=400,
                detail=f"Jenis stock '{item.jenis_stock}' tidak ditemukan"
            )
        order_stock = Belanja(
            ID=new_id,
            Jenis=item.jenis_stock,
            Jmlh=item.qty,
            Price=0,
            Unit=jenis_db.Unit,
            Divisi="",
            Checked=False,
            ket=item.keterangan_jenis_stock
        )
    
        session.add(order_stock)
    session.commit()
    session.refresh(new_order)
    return{
        "data":new_order 
    }



@router.put("/")
def update_belanja(
     request: belanja_item_request.BelanjaItemRequest, session: SessionDB1
):

    # cari data
    data = session.exec(
        select(Belanja).where(Belanja.ID == request.id, Belanja.Jenis == request.jenis_stock)
    ).first()
    print(data)

    # cek ada atau tidak
    if data is None:
        raise HTTPException(
            status_code=404,
            detail="Data tidak ditemukan"
        )

    # update field
    data.ket = request.keterangan_jenis_stock
    data.Jmlh = request.qty

    # simpan
    session.add(data)
    session.commit()
    session.refresh(data)

    return {
        "message": "Berhasil update",
        "data": data
    }

