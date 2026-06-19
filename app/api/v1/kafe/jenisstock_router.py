from fastapi import APIRouter,Depends
from app.auth import get_current_user
from app.database import SessionDBKafe
from sqlmodel import select,func
from app.model.kafe.jnsstock import Jnsstock

router = APIRouter()
def get_latest_id(session: SessionDBKafe):
    query = select(func.max(Jnsstock.ID))
    lates_id= session.exec(query).first()
    return lates_id if lates_id is not None else 0
def generate_new_id(session: SessionDBKafe):
    latest_id = get_latest_id(session)
    return latest_id + 1

@router.post("/post")
def create(jnsstock: Jnsstock, session: SessionDBKafe,current_user: dict = Depends(get_current_user)):
    jnsstock.ID = generate_new_id(session)
    session.add(jnsstock)
    session.commit()
    session.refresh(jnsstock)
    return {"message": "jenis stock created successfully"}

@router.get("/")
def get(session: SessionDBKafe,search: str = None,limit: int = 10, offset: int = 0,current_user: dict = Depends(get_current_user)):
    query = select(Jnsstock).offset(offset).limit(limit)
    if search:
        query = query.where(Jnsstock.Jenis.like(f"%{search}%"))
    results = session.exec(query).all()
    query_total = select(func.count(Jnsstock.ID))
    if search:
        query_total = query_total.where(Jnsstock.Jenis.like(f"%{search}%")) 
    total = session.exec(query_total).first()
    return {"data": results,
            "paging": {
                "limit": limit,
                "offset": offset,
                "total": total
            }}
@router.get("/{jenis}")
def get_by_jenis(jenis: str, session: SessionDBKafe,current_user: dict = Depends(get_current_user)):
    query = select(Jnsstock).where(Jnsstock.Jenis.like(f"%{jenis}%"))
    results = session.exec(query).all()
  
    return {"data": results}
