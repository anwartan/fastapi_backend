import select
from unittest import result

from fastapi import APIRouter, Depends, FastAPI
import app
from app.database import SessionDB1, get_session
from sqlmodel import Session, select,func
from app.model.kafe.bboreder import Bborder
from app.model.kafe.orderstock import Orderstock
router = APIRouter()

    
# @router.get("/")
# def get(session: SessionDB1,limit: int = 10, offset: int = 0, category: str = None):
#     query = select(Bborder).where(Bborder.Category == category).limit(limit).offset(offset)
#     results = session.exec(query).all()
#     query_total = select(func.count(Bborder.IDOrder)).where(Bborder.Category == category)
#     total = session.exec(query_total).first()
    
#     return {"data": results,
#             "paging": {
#                 "limit": limit,
#                 "offset": offset,
#                 "total": total
#             }}


@router.get("/")
def get_bborder(session: Session = Depends(get_session)):
    try:
        subquery = (
            select(func.count(Orderstock.IDOrder))
            .where(Orderstock.IDOrder == Bborder.IDOrder)
            .correlate(Bborder)
            .scalar_subquery()
        )

        query = select(
                Bborder,
                func.coalesce(subquery, 0).label("total_items")
            ).where(Bborder.Checked==False).limit(100).order_by(Bborder.IDOrder.desc())

        

        results = session.exec(query).all()

        data = []
        for bborder, total in results:
            item = bborder.dict()    
            item["total_items"] = total
            data.append(item)

        return  {"data": data,
                "paging": {
                 "total": total
             }}

    except Exception as e:
        return {"error": str(e)}    


@router.get("/{Category}/{Tanggal}")
def GetBYCategoryAndTanggal(session:SessionDB1,Category:str,Tanggal:str):
    
    query = select(Bborder).where(Bborder.Category   == Category, Bborder.Tgl == Tanggal)
    results = session.exec(query).first()
    if not results:
        latest_query = select(func.max(Bborder.IDOrder))
        latest_result = session.exec(latest_query).first()
        if latest_result is  None:
            current_id = 1
        else:
            current_id = latest_result + 1
        new_bborder = Bborder(IDOrder=current_id, Category=Category, Tgl=Tanggal, Total=0, Aktif=True, Inputer=0, Checked=False, ID_Check=0, Ket="")
        session.add(new_bborder)
        session.commit()
        querysearch = select(Bborder).where(Bborder.IDOrder == latest_result)
        results = session.exec(querysearch).first()
        return {"message": "Data tidak ditemukan"}
    return {"data": results}
@router.get("/{Category}")
def get(session: SessionDB1,Category:str,limit: int = 10, offset: int = 0):
    query = select(Bborder).limit(limit).offset(offset).where(Bborder.Category == Category).order_by(Bborder.IDOrder.desc())

    results = session.exec(query).all()
    query_total = select(func.count(Orderstock.IDOrder))
    total = session.exec(query_total).all()
    return {"data": results,
            "paging": {
                "limit": limit,
                "offset": offset,
                "total": total
            }}