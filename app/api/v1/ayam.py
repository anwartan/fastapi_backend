import select

from fastapi import APIRouter
from app.database import SessionDB1
from app.model.ayam import Ayam
from sqlmodel import select

router = APIRouter()


@router.post("/")
def create(ayam: Ayam, session: SessionDB1):
    return {"message": "Ayam created successfully"}

@router.get("/")
def get(session: SessionDB1):
    
    results = session.exec(select(Ayam)).all()
    return {"data": results}

@router.put("/")
def update(ayam: Ayam, session: SessionDB1):
    return {"message": "Ayam updated successfully"}

@router.delete("/")
def delete(ayam: Ayam, session: SessionDB1):
    return {"message": "Ayam deleted successfully"}