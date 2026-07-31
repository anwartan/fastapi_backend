import select

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import Subquery
from app.api.v1.kafe.belanja_router import get_media_service
from app.auth import get_current_user
from app.database import SessionDBKafe
from sqlmodel import select,func

from app.model.kafe.Media import Media
from app.model.kafe.Pricedetail import Pricedetail
from app.model.kafe.bboreder import Bborder
from app.model.kafe.jnsstock import Jnsstock
from app.model.kafe.member import Member
from app.request import pengiriman_order_stock
from app.request.createOrderRequestJenisStock import CreateOrderStockRequest
from datetime import datetime 
from app.model.kafe.orderstock import Orderstock
from app.request import orderStockItemRequest
from app.request.penerimaan_orderstock_request import InputPenerimaanOrderstockRequest
from app.request.pengiriman_order_stock import PengirimanOrderStock
from app.services.cafe_file_service import CafeFileService
from app.services.firebase_service import FirebaseService
from app.services.media_service import MediaService
router = APIRouter()

    
@router.get("/")
def get(session: SessionDBKafe,current_user: dict = Depends(get_current_user)):
    query = select(Orderstock)
    results = session.exec(query).all()
    query_total = select(func.count(Orderstock.IDOrder))
    total = session.exec(query_total).first()
    return {"data": results,
            "paging": {
        
                "total": total
            }}
@router.get("/{id}")
def get_by_id(id:int,session: SessionDBKafe,current_user: dict = Depends(get_current_user)):
    query = select(Orderstock).where(Orderstock.IDOrder == id).where(Orderstock.Checked==0)
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
@router.get("/{jenis}/get_harga_stock")
def get_harga_stock(
    jenis: str,
    session: SessionDBKafe,
    current_user: Member = Depends(get_current_user)
):
    query = (
        select(Pricedetail.Jmlh)
        .join(
            Orderstock,
            Orderstock.Jenis == Pricedetail.Jenis
        )
        .where(Orderstock.Jenis == jenis)
        .order_by(Pricedetail.ID_PriceDetail.desc())

    )

    harga = session.exec(query).first()

    if harga is None:
        raise HTTPException(
            status_code=404,
            detail="Harga tidak ditemukan"
        )

    return {"data": harga}

@router.post("/create")
def create(session: SessionDBKafe, order:CreateOrderStockRequest,bgTask: BackgroundTasks,current_user: Member = Depends(get_current_user)):
    new_id = get_latest_id(session,current_user) + 1
    date=datetime.strptime(order.tgl, "%Y-%m-%d").date()    
    new_order = Bborder(
        IDOrder=new_id,
        Tgl=date,
        Total=0,
        Aktif=True,
        Inputer=current_user.ID,
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

        order_stock = Orderstock(
            Tgl=date,
            IDOrder=new_id,
            Jenis=item.jenis_stock,
            Jmlh=item.qty,
            JmlhInp=0,
            unit=jenis_db.Unit,
            Divisi=current_user.Divisi,
            Inputer=current_user.ID,
            Checked=False,
            Ket=item.keterangan_jenis_stock,
            JmlhPengiriman=0.0,
            ID_Penerimaan=0,
        )
        session.add(order_stock)
    session.commit()
    session.refresh(new_order)
    message = f"{current_user.Nama} membuat order baru."
    bgTask.add_task(on_create_order_stock, message, new_order)
    return{
        "data":new_order 
    }

def on_create_order_stock(message: str, new_order: Bborder):
    FirebaseService.send_to_topic("order_stock_notification", "Order Stock Baru", message, {
        "type":"order_stock",
        "id": str(new_order.IDOrder),
    })
@router.delete("/{id}/{jenis}")
def delete(id: int,jenis: str, session: SessionDBKafe,current_user: Member = Depends(get_current_user)):
    query = select(Orderstock).where(Orderstock.IDOrder == id, Orderstock.Jenis == jenis).where(Orderstock.JmlhInp==0).where(Orderstock.Inputer==current_user.ID)
    result = session.exec(query).first()
    if not result:
        raise HTTPException(
            status_code=403,
            detail="Hanya pembuat order yang dapat menghapus data."
        )
    
    session.delete(result)
    session.commit()
    return {"message": "order stock deleted successfully"}
@router.put("/")
def update_orderstock(
     request: orderStockItemRequest.OrderStockItemRequest, session: SessionDBKafe,current_user: Member = Depends(get_current_user)
):

    # cari data
    data = session.exec(
        select(Orderstock).where(Orderstock.IDOrder == request.id, Orderstock.Jenis == request.jenis_stock).where(Orderstock.JmlhInp==0).where(Orderstock.Inputer==current_user.ID)
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
    current_user: Member = Depends(get_current_user),
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

    if input_orderstock is None:
        return {
            "message": "Data tidak ditemukan"
        }
    if input_orderstock is None:
        return {
            "message": "Data tidak ditemukan"
        }
    if input_orderstock.JmlhInp != 0 or input_orderstock.ID_Penerimaan != 0:
        return {
            "message": "Data sudah terisi"
        }
    input_orderstock.JmlhInp = penerimaan.JmlhPenerimaan
    input_orderstock.ID_Penerimaan=current_user.ID

    if(len(files) > 1):
        return{
            "message":"tidak boleh lebih dari 1"
        }
    
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
@router.get("/penerimaan/{id}")
def get_penerimaan_by_id(id: int,  session: SessionDBKafe,current_user: dict = Depends(get_current_user)):
    query = select(Orderstock).where(Orderstock.ID_OrderStock == id, Orderstock.JmlhInp != 0)
    result = session.exec(query).all()
    if not result:
        return JSONResponse(content={"message": "belanja not found"}, status_code=404)
    else:
        return {"data": result}
@router.get("/{id}/jenis")
def get_by_jenis(id: int,  session: SessionDBKafe, current_user: dict = Depends(get_current_user) ):
   
    query = select(Orderstock).where(Orderstock.IDOrder == id).where(Orderstock.JmlhInp == 0.0).where(Orderstock.JmlhInp==0)
    results = session.exec(query).all()
    result_mapped = []
    for result in results:
        result_mapped.append(result.Jenis)
    query_jenis = select(Jnsstock).where(Jnsstock.Jenis.in_(result_mapped))
    result_jenis = session.exec(query_jenis).all()
    return {"data": result_jenis}
@router.put("/reset-penerimaan-stock-item/{id}")
def reset_penerimaan_item(
    id: int,
    session: SessionDBKafe,
    current_user: Member = Depends(get_current_user)
):
    orderstock = session.exec(
        select(Orderstock).where(Orderstock.ID_OrderStock == id)
    ).first()

    if orderstock is None:
        raise HTTPException(
            status_code=404,
            detail="Data tidak ditemukan."
        )

    medias = session.exec(
        select(Media).where(
            Media.SubjectId == id,
            Media.SubjectType == Orderstock.subject_type()
        )
    ).all()

    for media in medias:
        session.delete(media)

    orderstock.JmlhInp = 0
    orderstock.Inputer = 0

    session.add(orderstock)

    session.commit()
    session.refresh(orderstock)

    return {
        "message": "Item penerimaan berhasil direset"
    }
@router.get("/{id}/jenis/pengiriman")
def get_by_jenis_pengiriman(id: int,  session: SessionDBKafe, current_user: dict = Depends(get_current_user) ):
   
    query = select(Orderstock).where(Orderstock.IDOrder == id).where(Orderstock.JmlhPengiriman == 0.0).where(Orderstock.JmlhPengiriman==0)
    results = session.exec(query).all()
    result_mapped = []
    for result in results:
        result_mapped.append(result.Jenis)
    query_jenis = select(Jnsstock).where(Jnsstock.Jenis.in_(result_mapped))
    result_jenis = session.exec(query_jenis).all()
    return {"data": result_jenis}
@router.put("/pengiriman-stock")
def pengirimanstock(
    session:SessionDBKafe,
    request:pengiriman_order_stock.PengirimanOrderStock,
    current_user:Member=Depends(get_current_user),
    
):
    query=select(Orderstock).where(Orderstock.IDOrder==request.id).where(Orderstock.Jenis==request.jenis)
    Subquery=session.exec(query).first()
    if Subquery is None:
            raise HTTPException(
                status_code=404,
                detail="Data tidak ditemukan"
            )
    Subquery.JmlhPengiriman = request.jmlhpengiriman
    session.add(Subquery)
    session.commit()
    session.refresh(Subquery)

    return {
        "message": "Berhasil update",
        "data": Subquery
    }

 