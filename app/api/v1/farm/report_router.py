import string

from annotated_types import T
from fastapi import APIRouter, Query
from httpcore import stream
from sqlalchemy import Integer, func, literal
from websockets import route

from app.database import SessionDB1
from app.model.farm import telurpro
from app.model.farm.TempJmlhAyam import TempJmlhAyam
from app.model.farm.ayam import Ayam
from app.model.farm.ayammini import Ayammini
from app.model.farm.mskanakayam import Mskanakayam
from app.model.farm.telurpro import Telurpro
from app.model.farm.datakandang import Datakandang
from sqlmodel import select, func, desc, literal_column
router = APIRouter()
@router.get("/{date}")
def reportayamperhari(session: SessionDB1, date:str):

    ayammini_sub_query = select(Mskanakayam.TglMsk, literal("Mini A").label("Kandang"),Ayammini.Jmlh, literal("0").cast(Integer).label("Jmlh"), literal("0").cast(Integer).label("persen"),Ayammini.JenisAyam.label("Jenisayam")).join(Ayammini, Ayammini.ID_kcl == Mskanakayam.ID).order_by(desc(Ayammini.Tgl)).limit(1)   
    ayammini_results = session.exec(ayammini_sub_query).all()

    ayam_sub_query = select(Ayam.ID,Ayam.Kandang,Mskanakayam.TglMsk,Ayam.Jenisayam).join(Ayammini, Ayammini.ID == Ayam.ID_Mini).join(Mskanakayam, Ayammini.ID_kcl == Mskanakayam.ID).subquery()
    TempJmlhAyam_sub_query = select(TempJmlhAyam.Kandang, TempJmlhAyam.Jmlh).where(TempJmlhAyam.Tgl == date).subquery()
    telurpro_sub_query = select(Telurpro.ID, Telurpro.Jmlh,Telurpro.Persen).where(Telurpro.Tgl == date).subquery()
    statement = select(ayam_sub_query.c.TglMsk,TempJmlhAyam_sub_query.c.Kandang, TempJmlhAyam_sub_query.c.Jmlh, telurpro_sub_query.c.Jmlh, telurpro_sub_query.c.Persen, ayam_sub_query.c.Jenisayam
    ).join(TempJmlhAyam_sub_query, TempJmlhAyam_sub_query.c.Kandang == ayam_sub_query.c.Kandang
    ).join(telurpro_sub_query, telurpro_sub_query.c.ID == ayam_sub_query.c.ID)
    results = session.exec(statement).all()
    mix = ayammini_results + results


    return {"data": [{"Tgl": mix[0], "Kandang": mix[1], "Jmlh": mix[2], "JmlhPro": mix[3], "persen":mix[4], "jenis":mix[5]} for mix in mix]}

