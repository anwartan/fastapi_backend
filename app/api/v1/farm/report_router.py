from fastapi import APIRouter
from requests import session
from sqlalchemy import Integer, Subquery, func, literal, desc, null
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from app.database import SessionDB1
from app.model.farm.TempLangsirMkn import TempLangsirMkn
from app.model.farm.TempJmlhAyam import TempJmlhAyam
from app.model.farm.ayam import Ayam
from app.model.farm.ayamklr import Ayamklr
from app.model.farm.ayammini import Ayammini
from app.model.farm.datakandang import Datakandang
from app.model.farm.harga import Harga
from app.model.farm.mskanakayam import Mskanakayam
from app.model.farm.telurklr import Telurklr
from app.model.farm.telurpro import Telurpro 
from app.model.farm.perubahandataayam import PerubahanDataAyam
from app.model.farm.TempPickTelur import TempPickTelur
from sqlmodel import select, func, desc

from app.model.farm.telursisa import Telursisa
from app.model.farm.telursisaarab import Telursisaarab
router = APIRouter()
@router.get("/sisaproluar/{date}")
def sisaproluar(session: SessionDB1, date:str):
    layer_statement = select(Telursisa.JmlhLap, Telursisa.JmlhMlm).where(Telursisa.Tgl == date)
    data__layer = session.exec(layer_statement).first()
    jmlh_lap_layer = 0 
    jmlh_mlm_layer = 0
    if data__layer is not None:
        jmlh_lap_layer = data__layer.JmlhLap
        jmlh_mlm_layer = data__layer.JmlhMlm
    
    arab_statement = select(Telursisaarab.JmlhLap, Telursisaarab.JmlhMlm).where(Telursisaarab.Tgl == date)
    data__arab = session.exec(arab_statement).first()
    jmlh_lap_arab = 0
    jmlh_mlm_arab = 0
    if data__arab is not None:
        jmlh_lap_arab = data__arab.JmlhLap
        jmlh_mlm_arab = data__arab.JmlhMlm

      

    return {
        "data": [
            {
                "tipe":"Layer",
                "lap": jmlh_lap_layer,
                "mlm": jmlh_mlm_layer,
            },
            {
                "tipe":"arab",
                "lap": jmlh_lap_arab,
                "mlm": jmlh_mlm_arab,
            }
        ]
    }
@router.get("/langsirmkn/{date}")
def langsirmkn(session: SessionDB1, date : str, dist : str = None, kandang : str = None):
    statement = select(TempLangsirMkn.Dist, TempLangsirMkn.Kandang, TempLangsirMkn.JenisMkn, TempLangsirMkn.Goni, TempLangsirMkn.Kg, TempLangsirMkn.Input).where(TempLangsirMkn.Tgl == date)
    if dist is not None :
        statement = statement.where(TempLangsirMkn.Dist == dist)
    if kandang is not None :
        statement = statement.where(TempLangsirMkn.Kandang == kandang).indexing()
    results = session.exec(statement).all()
    return{
        "data":[
            {
                "Dist": item.Dist,
                "kandang": item.Kandang,
                "JenisMkn": item.JenisMkn,
                "Goni": item.Goni,
                "Kg": item.Kg,
                "Input": item.Input,
            }
            for item in results
        ]
    }
    
@router.get("/langsirtelur/{date}")
def langsirtelur(session: SessionDB1, date = str,  dist : str = None, kandang : str = None):
    statement = select(
        Ayam.Indexing.label("Kandang_ID"),
        TempPickTelur.Dist, 
        TempPickTelur.Kandang, 
        TempPickTelur.Ikat, 
        TempPickTelur.Ppn, 
        TempPickTelur.Butir, 
        TempPickTelur.Tipe,
          TempPickTelur.Jenisayam, TempPickTelur.Input
        ).where(TempPickTelur.Tgl == date
        ).join(Ayam, Ayam.Kandang == TempPickTelur.Kandang)

    if dist is not None :
        statement = statement.where(TempPickTelur.Dist == dist)
    if kandang is not None :
        statement = statement.where(TempPickTelur.Kandang == kandang)
    results = session.exec(statement).all()
    return {
        "data": [
            {
                "Kandang_ID": item[0],
                "Dist": item[1],
                "kandang": item[2],
                "Ikat": item[3],
                "Ppn": item[4],
                "Butir": item[5],
                "Tipe": item[6],
                "Jenisayam": item[7],
                "Input": item[8],

            }
            for item in results
        ]
    }
@router.get("/telur-klr/{date}")
def telurklrlayer(session: SessionDB1, date: str):
    statement = select(
        Telurklr.Nama,
        Telurklr.Jmlh,
        Telurklr.JenisTelur
    ).where(
        Telurklr.Tgl == date
    ).order_by( Telurklr.Nama,
    Telurklr.JenisTelur)

    data = session.exec(statement).all()

    return {
        "data": [
            {
                "Nama": item.Nama,
                "Jmlh": item.Jmlh,
                "JenisTelur": item.JenisTelur,
            }
            for item in data
        ]
    }
@router.get("/sisa-telur/{date}")
def telursisalayer(session: SessionDB1, date:str):
    layer_statement = select(Telursisa.JmlhLap, Telursisa.JmlhMlm).where(Telursisa.Tgl == date)
    data__layer = session.exec(layer_statement).first()
    arab_statement = select(Telursisaarab.JmlhLap, Telursisaarab.JmlhMlm).where(Telursisaarab.Tgl == date)
    data__arab = session.exec(arab_statement).first()
    return {
        "data": [
            {
                "tipe":"Layer",
                "lap": data__layer.JmlhLap,
                "mlm": data__layer.JmlhMlm,
            },
            {
                "tipe":"arab",
                "lap": data__arab.JmlhLap,
                "mlm": data__arab.JmlhMlm,
            }
        ]
    }
@router.get("/harga/range")
def harga_by_range(session: SessionDB1, start_date: str | None, end_date: str | None):
    print(f"Received: start_date={start_date}, end_date={end_date}")

    if start_date == "":
        start_date = None
    if end_date == "":
        end_date = None

    subquery_query = select(Harga.Jenis, func.max(Harga.Tgl).label("max_tgl"))

    if start_date is not None:
        subquery_query = subquery_query.where(Harga.Tgl >= start_date)
    if end_date is not None:
        subquery_query = subquery_query.where(Harga.Tgl <= end_date)

    subquery = subquery_query.group_by(Harga.Jenis).subquery()

    statement = (
        select(Harga.Harga, Harga.Jenis, Harga.Tgl)
        .join(subquery, (Harga.Jenis == subquery.c.Jenis) & (Harga.Tgl == subquery.c.max_tgl))
        .order_by(Harga.Tgl.desc())
    )

    result = session.exec(statement).all()
    print(f"Result count: {len(result)}")
    return [{"Harga": r.Harga, "Jenis": r.Jenis, "Tgl": str(r.Tgl)} for r in result]
@router.get("/hargainput/{date}")
def inputharga(session: SessionDB1, date:str):
    Subquery = select(Harga.Jenis).where(Harga.Tgl == date)
    result = session.exec(Subquery).all()
    return result
@router.get("/hargaluar")
def hargaluar(session: SessionDB1):
    statement = select(Harga.Jenis, Harga.Harga).where(Harga.Jenis == "Telur").order_by(Harga.Tgl.desc())
    result = session.exec(statement).first()
    subquery = select(Harga.Jenis, Harga.Harga).where(Harga.Jenis == "Telur Arab").order_by(Harga.Tgl.desc())
    result_arab = session.exec(subquery).first()
    data = []
    if result:
        data.append({
            "jenis": result.Jenis,
            "harga": result.Harga,
        })
    if result_arab:
        data.append({
            "jenis": result_arab.Jenis,
            "harga": result_arab.Harga,
        })          
    return [
    {"Jenis": result.Jenis, "Harga": result.Harga},
    {"Jenis": result_arab.Jenis, "Harga": result_arab.Harga},
]
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