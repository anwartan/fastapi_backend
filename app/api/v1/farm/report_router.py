from fastapi import APIRouter
from sqlalchemy import Integer, func, literal, desc
from datetime import datetime
from app.database import SessionDB1
from app.model.farm.TempJmlhAyam import TempJmlhAyam
from app.model.farm.ayam import Ayam
from app.model.farm.ayamklr import Ayamklr
from app.model.farm.ayammini import Ayammini
from app.model.farm.mskanakayam import Mskanakayam
from app.model.farm.telurpro import Telurpro 
from app.model.farm.perubahandataayam import PerubahanDataAyam
from sqlmodel import select, func, desc
router = APIRouter()
@router.get("/{date}")
def reportayamperhari(session: SessionDB1, date:str, filter: str = "kandang"):
    print("date", date)
    print("filter", filter)
    ayammini_sub_query = select(Mskanakayam.TglMsk, literal("Mini A").label("Kandang"),Ayammini.Jmlh, literal("0").cast(Integer).label("Jmlh"), literal("0").cast(Integer).label("persen"),Ayammini.JenisAyam.label("Jenisayam"), literal("0").cast(Integer).label("Indexing"),literal("0").cast(Integer).label("ID") ).join(Ayammini, Ayammini.ID_kcl == Mskanakayam.ID).order_by(desc(Ayammini.Tgl)).limit(1)   
    ayammini_results = session.exec(ayammini_sub_query).all()

    ayam_sub_query = select(Ayam.ID,Ayam.Kandang,Mskanakayam.TglMsk,Ayam.Jenisayam).join(Ayammini, Ayammini.ID == Ayam.ID_Mini).join(Mskanakayam, Ayammini.ID_kcl == Mskanakayam.ID).subquery()

    TempJmlhAyam_sub_query = select(TempJmlhAyam.Kandang, TempJmlhAyam.Indexing).where(TempJmlhAyam.Tgl == date).subquery()

    telurpro_sub_query = select(Telurpro.ID, Telurpro.Jmlh,Telurpro.Persen).where(Telurpro.Tgl == date).subquery()
    sub_perubahan_data_ayam = select(PerubahanDataAyam.ID, PerubahanDataAyam.JmlhSkrg, PerubahanDataAyam.Tgl, func.row_number().over(partition_by=PerubahanDataAyam.ID, order_by=PerubahanDataAyam.Tgl.desc()).label("rn")).where(PerubahanDataAyam.Tgl <= date).subquery()
    
    selected_date = datetime.strptime(date, "%Y-%m-%d").date()

    start_of_month = selected_date.replace(day=1)
   
    if selected_date == start_of_month:
        start_of_month = selected_date.replace(month=selected_date.month - 1, day=1)

    sub_jlh_klr = select(Ayamklr.ID, func.sum(Ayamklr.mati +Ayamklr.sakit +Ayamklr.jual).label("jlh_klr")).join(Ayam, Ayam.ID == Ayamklr.ID).where(Ayamklr.Tgl >= start_of_month, Ayamklr.Tgl < date).group_by(Ayamklr.ID).subquery()
    sub_ayam_sekarang = select(sub_perubahan_data_ayam.c.ID, sub_perubahan_data_ayam.c.JmlhSkrg, func.coalesce(sub_jlh_klr.c.jlh_klr, 0).label("jlh_klr"), 
                               (sub_perubahan_data_ayam.c.JmlhSkrg - func.coalesce(sub_jlh_klr.c.jlh_klr, 0)).label("JmlhSkrgIncKlr")
                                ).join(sub_jlh_klr, sub_jlh_klr.c.ID == sub_perubahan_data_ayam.c.ID, isouter=True).where(sub_perubahan_data_ayam.c.Tgl <= date).where(sub_perubahan_data_ayam.c.rn == 1).subquery()
    print("sub_ayam_sekarang", sub_ayam_sekarang)
    statement = select(ayam_sub_query.c.TglMsk,TempJmlhAyam_sub_query.c.Kandang, sub_ayam_sekarang.c.JmlhSkrgIncKlr ,telurpro_sub_query.c.Jmlh, telurpro_sub_query.c.Persen, ayam_sub_query.c.Jenisayam, TempJmlhAyam_sub_query.c.Indexing, ayam_sub_query.c.ID
    ).join(TempJmlhAyam_sub_query, TempJmlhAyam_sub_query.c.Kandang == ayam_sub_query.c.Kandang
    ).join(telurpro_sub_query, telurpro_sub_query.c.ID == ayam_sub_query.c.ID
    ).join(sub_ayam_sekarang, sub_ayam_sekarang.c.ID == ayam_sub_query.c.ID)
   
    if(filter == "ID"):
        statement = statement.order_by(ayam_sub_query.c.ID.asc())
    else:
        statement = statement.order_by(TempJmlhAyam_sub_query.c.Indexing.asc())

    results = session.exec(statement).all()
    mix = ayammini_results + results
    print("hasil", mix)

    return {"data": [{"Tgl": mix[0], "Kandang": mix[1], "Jmlh": mix[2], "JmlhPro": mix[3], "persen":mix[4], "jenis":mix[5], "ID":mix[7]} for mix in mix]}

