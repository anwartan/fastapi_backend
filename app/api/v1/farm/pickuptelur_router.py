
from datetime import date
from fastapi import APIRouter
from app.database import SessionDB1
from app.model.farm.TempPickupTelur import TempPickUpTelur
from app.request.pickuptelur_request import Pickuptelurrequest
from app.request.create_pickuptelur_request import Createpickuptelurrequest
from sqlmodel import select


router = APIRouter()
@router.post("/")
def create(request: Createpickuptelurrequest, session:SessionDB1):
    now = date.today().strftime("%Y-%m-%d")
    for item in request.data:
        pickuptelur = TempPickUpTelur(
            Tgl= now,
            Dist= 1,
            Kandang= item.kandang,
            Ikat= item.ikat,
            Ppn= item.papan,
            Butir= item.butir,
            Tipe= item.tipe,
            Jenisayam= item.jenis_ayam,
            Input=0

        )
        session.add(pickuptelur)
    session.commit()

    return{"message":"pick up telur created succesfull"}

@router.get("/{date}")
def get(session:SessionDB1, date: str):
    pickuptelur_query = select(TempPickUpTelur).where(TempPickUpTelur.Tgl == date)
    pickuptelur = session.exec(pickuptelur_query).all()
    return {"data":pickuptelur}



