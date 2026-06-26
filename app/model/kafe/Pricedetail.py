from datetime import date

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Pricedetail(SQLModel, table=True):
    __tablename__ = "pricedetail"
    ID_PriceDetail:int = Field(default=None, primary_key=True)
    Tgl: date=Field(default=None)
    Jenis: str=Field(default=None)
    Jmlh: int=Field(default=None)
    Inputer: int=Field(default=None)