import select
from unittest import result

from fastapi import APIRouter, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
import app
from app.api.v1.kafe import bborder
from app.api.v1.kafe.belanja_router import get_media_service
from app.auth import get_current_user
from app.database import SessionDBKafe
from sqlmodel import Date, select,func

from app.model.kafe import orderstock
from app.model.kafe.bboreder import Bborder
from app.model.kafe.jnsstock import Jnsstock
from app.model.kafe.orderstock import Orderstock
from app.request.createOrderRequestJenisStock import CreateOrderStockRequest
from datetime import datetime 
from app.model.kafe.orderstock import Orderstock
from app.request import orderStockItemRequest
from app.request.penerimaan_orderstock_request import InputPenerimaanOrderstockRequest
from app.services.cafe_file_service import CafeFileService
from app.services.media_service import MediaService
router = APIRouter()

    
@router.get("/")
def get(session: SessionDBKafe, limit: int = 10, offset: int = 0,current_user: dict = Depends(get_current_user)):
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
def get_by_id(id:int,session: SessionDBKafe,current_user: dict = Depends(get_current_user)):
    query = select(Orderstock).where(Orderstock.IDOrder == id)
    result = session.exec(query).all()
    if result is None:
        return JSONResponse(content={"message": "belanja not found"}, status_code=404)
    else:       
        return {"data": result}
    

    return {"data": result} 
def get_latest_id(session: SessionDBKafe,current_user: dict = Depends(get_current_user)):
    query = select(func.max(Bborder.IDOrder))
    latest_id= session.exec(query).first()
    return latest_id if latest_id is not None else 0


@router.post("/create")
def create(session: SessionDBKafe, order:CreateOrderStockRequest,current_user: dict = Depends(get_current_user)):
    new_id = get_latest_id(session,current_user) + 1
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
            JmlhPenerimaan=0,
            Inputer=0,
            Checked=False,
            Ket=item.keterangan_jenis_stock         )
        session.add(order_stock)
    session.commit()
    session.refresh(new_order)
    return{
        "data":new_order 
    }
@router.delete("/{id}/{jenis}")
def delete(id: int,jenis: str, session: SessionDBKafe,current_user: dict = Depends(get_current_user)):
    query = select(Orderstock).where(Orderstock.IDOrder == id, Orderstock.Jenis == jenis)
    result = session.exec(query).first()
    if not result:
        raise HTTPException(status_code=404, detail="order stock not found")
    session.delete(result)
    session.commit()
    return {"message": "order stock deleted successfully"}
@router.put("/")
def update_orderstock(
     request: orderStockItemRequest.OrderStockItemRequest, session: SessionDBKafe,current_user: dict = Depends(get_current_user)
):

    # cari data
    data = session.exec(
        select(Orderstock).where(Orderstock.IDOrder == request.id, Orderstock.Jenis == request.jenis_stock)
    ).first()
    print("Model",data)
    print("Request",request)

    # cek ada atau tidak
    if data is None:
        raise HTTPException(
            status_code=404,
            detail="Data tidak ditemukan"
        )

    # update field
    data.Ket = request.keterangan_jenis_stock
    data.Jmlh = request.qty

    # simpan
    session.add(data)
    session.commit()
    session.refresh(data)

    return {
        "message": "Berhasil update",
        "data": data
    }
@router.put("/penerimaan/")
async def penerimaan_orderstock(
    session: SessionDBKafe,
    penerimaan: InputPenerimaanOrderstockRequest = Depends(
        InputPenerimaanOrderstockRequest.as_form
    ),
    current_user: dict = Depends(get_current_user),
    files: list[UploadFile] = File(...),
    mediaService: MediaService = Depends(get_media_service) 
):
   
    input_orderstock = (
        session.query(Orderstock)
        .filter(
            Orderstock.IDOrder == penerimaan.id,
            Orderstock.Jenis == penerimaan.Jenis
        )
        .first()
    )

    # jika data tidak ditemukan
    if input_orderstock is None:
        return {
            "message": "Data tidak ditemukan"
        }

    # update data
    input_orderstock.JmlhPenerimaan = penerimaan.JmlhPenerimaan

    # optional
    
    
    uploaded_files = await CafeFileService.massUpload(files)


    # simpan perubahan
    session.commit()
    session.refresh(input_orderstock)
    print(f"Input Orderstock ID after commit: {input_orderstock.ID_OrderStock}")

    mediaService.createMany(uploaded_files,Orderstock.subject_type(), input_orderstock.ID_OrderStock)

    return {
        "message": "Data berhasil diupdate",
        "data": 
            input_orderstock
        }
@router.get("/{id}/jenis")
def get_by_jenis(id: int,  session: SessionDBKafe, current_user: dict = Depends(get_current_user) ):
   
    query = select(Orderstock).where(Orderstock.IDOrder == id).where(Orderstock.JmlhPenerimaan == 0)
    results = session.exec(query).all()
    result_mapped = []
    for result in results:
        result_mapped.append(result.Jenis)
    query_jenis = select(Jnsstock).where(Jnsstock.Jenis.in_(result_mapped))
    result_jenis = session.exec(query_jenis).all()
    return {"data": result_jenis}
