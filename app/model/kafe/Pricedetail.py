from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Pricedetail(SQLModel, table=True):
    __tablename__ = "pricedetail"
    Tgl: str
    Jenis: str
    Jmlh: int
    Inputer: int