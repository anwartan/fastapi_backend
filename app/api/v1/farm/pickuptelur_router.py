
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy import func
from app.auth import get_current_user_farm
from app.database import SessionDB1
from app.model.farm.TempPickupTelur import TempPickUpTelur
from app.model.farm.ayam import Ayam
from app.request.create_pickuptelur_request import Createpickuptelurrequest
from sqlmodel import select

from app.request.pickuptelur_request import Pickuptelurrequest


router = APIRouter()
def get_latest_id(session: SessionDB1):
    query = select(func.max(TempPickUpTelur.id))
    latest_id= session.exec(query).first()
    return latest_id if latest_id is not None else 0
@router.get("/option")
def getOption(session:SessionDB1):
    getkandang_qury= select(Ayam.Kandang, Ayam.Jenisayam).order_by(Ayam.Indexing)
    data_kandang = session.exec(getkandang_qury).all()
    
    mapped_data_kandang = []
    for item in data_kandang:
        mapped_data_kandang.append({
            "kandang": item.Kandang,
            "jenis_ayam": item.Jenisayam
        })
    return {
        "data": mapped_data_kandang
    }
@router.post("/make")
def create(request: Pickuptelurrequest, session:SessionDB1, current_user = Depends(get_current_user_farm)):
    now = date.today().strftime("%Y-%m-%d")
    new_id = get_latest_id(session) + 1

    pickuptelur = TempPickUpTelur(
            id=new_id,
            Tgl=now,
            Dist= 1,
            Kandang= request.kandang,
            Ikat= request.ikat,
            Ppn= request.papan,
            Butir= request.butir,
            Tipe= request.tipe,
            Jenisayam= request.jenis_ayam,
            Input="0"

        )
    session.add(pickuptelur)
    session.commit()

    return{"message":"pick up telur created succesfull"}






    
    

