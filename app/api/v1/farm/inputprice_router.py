
from pydoc import text

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Subquery, select
from sqlalchemy.orm import Session, subqueryload
from app.api.v1.farm.request.input_harga_request import InputHargaRequest
from app.database import SessionDB1
from app.model.farm.harga import Harga
router = APIRouter()
@router.post("/addharga")
def add_harga(data: InputHargaRequest, session: SessionDB1):
    harga = Harga(Tgl=data.tanggal, Harga=data.harga, Jenis=data.jenis)
    session.add(harga)
    session.commit()

    return {
        "message": "Data berhasil disimpan"
    }
@router.put("/editharga/")
def edit_harga(data: InputHargaRequest, session: SessionDB1):
    edit_harga_query = select(Harga.Jenis, Harga.Harga).where(Harga.Tgl == data.tanggal and Harga.Jenis == data.jenis)
    result = session.exec(edit_harga_query).first()
    if result is None:
        harga = Harga(Tgl=data.tanggal, Harga=data.harga, Jenis=data.jenis)
        session.add(harga)
    else:
        result.Harga = data.harga
        session.add(result)
    session.commit()

    return {
        "message succesful"
    }
@router.delete("/deleteharga/")
def delete_harga(data: InputHargaRequest, session: SessionDB1):
    Subquery = select(Harga.Jenis, Harga.Harga).where(Harga.Tgl == data.Tgl and Harga.Jenis == data.Jenis)
    statement = session.exec(Subquery).first()
    if statement is None:
        raise HTTPException(status_code=400, detail="harga tidak di temukan")
    else:
        session.delete()
    session.commit()
    return {
        "message berhasil"
    }
@router.get("/getoption")
def addharga(session: SessionDB1):
    option_harga = select(Harga.Jenis)
    result = session.exec(option_harga).all()
    return {
        "data": {
            "jenis": i.Jenis,
        }
        for i in result
    }
