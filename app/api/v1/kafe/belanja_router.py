import select

from fastapi import APIRouter, HTTPException, BackgroundTasks,File,UploadFile, Depends
from app.auth import get_current_user
from app.database import SessionDBKafe, SessionDBKafeLogin
from sqlmodel import select,func
from app.model.kafe.belanja import Belanja
from app.model.kafe.bboreder import Bborder
from app.model.kafe.jnsstock import Jnsstock
from app.model.kafe.member import Member
from app.request import belanja_item_request, resetbelanjadetail
from app.request import belanjaan_detail_item_request
from app.request.create_order_request import CreateOrderRequest
from datetime import datetime 
from fastapi.responses import JSONResponse
from sqlmodel import select
from app.request.penerimaan_belanja_request import InputPenerimaanBelanjaRequest
from app.services.firebase_service import FirebaseService
from app.services.cafe_file_service import CafeFileService
from app.services.media_service import MediaService
router = APIRouter()
def get_latest_id(session: SessionDBKafe):
    query = select(func.max(Bborder.IDOrder))
    latest_id= session.exec(query).first()
    return latest_id if latest_id is not None else 0
def get_by_ids(session: SessionDBKafe, id: int,):
    query = select(Belanja).where(Belanja.ID == id)
    result = session.exec(query).all()
    if not result:
        raise HTTPException(status_code=404, detail="Belanja not found")
    return result

@router.get("/")
def get(session: SessionDBKafe, limit: int = 10, offset: int = 0,current_user: dict = Depends(get_current_user)):
    
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
def get_by_id(id:int,session: SessionDBKafe,current_user: dict = Depends(get_current_user)):
    
    query = select(Belanja).where(Belanja.ID == id)

    result = session.exec(query).all()
    
    if not result:
        return JSONResponse(content={"message": "belanja not found"}, status_code=404)
    else:
        return {"data": result}
    
@router.delete("/{id}/{jenis}")
def delete(id: int,jenis: str, session: SessionDBKafe,current_user: dict = Depends(get_current_user)):
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
def create(
    session: SessionDBKafe,
    order: CreateOrderRequest,
    bgTask: BackgroundTasks,
    current_user: Member = Depends(get_current_user),
):
   

    new_id = get_latest_id(session) + 1
    date = datetime.strptime(order.tgl, "%Y-%m-%d")

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

        order_belanja = Belanja(
            ID=new_id,
            Jenis=item.jenis_stock,
            JmlhOrder=item.qty,
            JmlhPenerima=0,
            ID_Penerima=0,
            Jmlh=0,
            ID_Belanja=0,
            Price=0,
            Unit=jenis_db.Unit,
            Divisi=current_user.Divisi,
            Checked=False,
            ket="",
            ID_UserBelanja=0
        )
        session.add(order_belanja)

    session.commit()
    session.refresh(new_order)

    # token1  = "cW0fJxjrSyWCh0GfyR7bSS:APA91bFee7OaT9QHGJFDNOGh5elQ1N5yjt66krKTgUEWmvHGJ0ECp913gHidoSRpbs1Feu2ej4_sYM4aViYf5pUCPND3E5XMxN_i4wS_WR49M7uNA6AILiI";
     # token3="cPuLbXpaT8OXj6BTU79y70:APA91bGZKSCm-kEGzZXZ4ddDTUgEZR-gsSHEbYDImi2Ot838evPwWElRTNGRdBGShP_7Ea2_Z3T_q5rytK1OchtINDfcTtMgtcyZIT0hGScTKuEMrhcYSdY";
    # FirebaseService.send_notification(token1, "New Order Created", "A new order has been created.") ## delay
    # FirebaseService.send_notification(token2, "New Order Created", "A new order has been created.") ## delay
    # # bgTask.add_task(order_stock_created_listener)
    print("Order created, background task added")
    return{
        "data":new_order 
    }



@router.put("/")
def update_belanja(
     request: belanja_item_request.BelanjaItemRequest, session: SessionDBKafe,current_user: dict = Depends(get_current_user)
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

@router.get("/{id}/jenis")
def get_by_jenis(id: int,  session: SessionDBKafe):
    query = select(Belanja).where(Belanja.ID == id).where(Belanja.JmlhPenerima == 0)
    results = session.exec(query).all()
    result_mapped = []
    for result in results:
        result_mapped.append(result.Jenis)
    query_jenis = select(Jnsstock).where(Jnsstock.Jenis.in_(result_mapped))
    result_jenis = session.exec(query_jenis).all()
    return {"data": result_jenis}


def get_media_service(session: SessionDBKafe) -> MediaService:
    return MediaService(session=session)

from fastapi import Depends, HTTPException, UploadFile, File

@router.put("/penerimaan/")
async def penerimaan_belanja(
    session: SessionDBKafe,
    penerimaan: InputPenerimaanBelanjaRequest = Depends(
        InputPenerimaanBelanjaRequest.as_form
    ),
    current_user: Member = Depends(get_current_user),
    files: list[UploadFile] = File(...),
    mediaService: MediaService = Depends(get_media_service) 
):
   
    input_Belanja = (
        session.query(Belanja)
        .filter(
            Belanja.ID == penerimaan.id,
            Belanja.Jenis == penerimaan.Jenis
        )
        .first()
    )

    if input_Belanja is None:
        return {
            "message": "Data tidak ditemukan"
        }

    # update data
    input_Belanja.JmlhPenerima = penerimaan.JmlhPenerima,
    input_Belanja.ID_Penerima=current_user.ID

    # optional
    
    
    uploaded_files = await CafeFileService.massUpload(files)


    # simpan perubahan
    session.commit()
    session.refresh(input_Belanja)
    print(f"Input Orderstock ID after commit: {input_Belanja.ID_Belanja}")

    mediaService.createMany(uploaded_files,Belanja.subject_type(), input_Belanja.ID_Belanja)

    return {
        "message": "Data berhasil diupdate",
        "data": 
            input_Belanja
        }
@router.put("/belanjaandetail/")
def belanjaandetail(
     request: belanjaan_detail_item_request.BelanjaanDetailItemRequest, session: SessionDBKafe,current_user: Member = Depends(get_current_user)
):

    # cari data
    data = session.exec(
        select(Belanja).where(Belanja.ID == request.id, Belanja.Jenis == request.jenis)
    ).first()
    print(data)

    # cek ada atau tidak
    if data is None:
        raise HTTPException(
            status_code=404,
            detail="Data tidak ditemukan"
        )

    # update field
    data.Price = request.harga
    data.Jmlh = request.qty
    data.ket = request.ket
    data.ID_UserBelanja = current_user.ID

    # simpan
    session.add(data)
    session.commit()
    session.refresh(data)

    return {
        "message": "Berhasil update",
        "data": data
    }
@router.put("/resetbelanjaandetail")
def reset_belanjaandetail(
    request: resetbelanjadetail.ResetBelanjaDetailRequest, session: SessionDBKafe,current_user: dict = Depends(get_current_user)
):

    # cari data
    data = session.exec(
        select(Belanja).where(Belanja.ID == request.id, Belanja.Jenis == request.jenis)
    ).first()
    print(data)

    # cek ada atau tidak
    if data is None:
        raise HTTPException(
            status_code=404,
            detail="Data tidak ditemukan"
        )

    # update field
    data.Price = 0
    data.Jmlh = 0
    data.ket = ""

    # simpan
    session.add(data)
    session.commit()
    session.refresh(data)

    return {
        "message": "Berhasil reset",
        "data": data
    }
@router.get("/belanjaandetail/{id}")
def get_belanjaandetail_by_id(id: int,  session: SessionDBKafe,current_user: dict = Depends(get_current_user)):
    query = select(Belanja).where(Belanja.ID == id, Belanja.Jmlh != 0, Belanja.Price != 0)
    result = session.exec(query).all()
    if not result:
        return JSONResponse(content={"message": "belanja not found"}, status_code=404)
    else:
        return {"data": result}
@router.get("/{id}/jenis/byjumlah")
def get_by_jenis_jumlah(id: int,  session: SessionDBKafe,current_user: dict = Depends(get_current_user)):
    query = select(Belanja).where(Belanja.ID == id).where(Belanja.Jmlh == 0)
    results = session.exec(query).all()
    result_mapped = []
    for result in results:
        result_mapped.append(result.Jenis)
    query_jenis = select(Jnsstock).where(Jnsstock.Jenis.in_(result_mapped))
    result_jenis = session.exec(query_jenis).all()
    return {"data": result_jenis}
