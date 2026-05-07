import select
from unittest import result

from fastapi import APIRouter, Query
from httpx import request
from app.database import SessionDB1
from app.model.farm import ayammini
from app.model.farm.ayamklr import Ayamklr
from app.model.farm.ayammini import Ayammini
from app.model.farm.ayam import Ayam
from sqlmodel import select, func

router = APIRouter()

@router.post("/")
def create(ayammini: Ayamklr, session:SessionDB1):
    return {"message": "Ayammini created success"}
@router.get("/")
def get(session:SessionDB1, limit: int = 10, offset: int = 0):
    query = select(Ayamklr).limit(limit).offset(offset)
    result = session.exec(query).all()

    query_total = select(func.count(Ayamklr.ID))
    total = session.exec(query_total).first()
    return {
        "data" : result,
        "paging" : {
            "limit": limit,
            "offset": offset,
            "total": total,

        }
    }
@router.get("/{id}")
def getbyid(session:SessionDB1, id:int):
    Query = select(Ayamklr).where(Ayamklr.ID == id)
    result = session.exec(Query).first()
    if result is None:
        return {"message": "Ayammini not found"}
    else:
        return{
            "data":result
        }
@router.put("/")
def update(ayamklr: Ayamklr, session:SessionDB1):
    return {"message": "Ayamklr updated success"}
@router.delete("/")
def delete(ayamklr: Ayamklr, session:SessionDB1):
    return {"message": "Ayamklr deleted success"}