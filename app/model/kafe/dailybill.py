from datetime import date

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class dailybill(SQLModel, table=True):
    __tablename__ = "dailybill"
    IDDailyBill: int = Field(default=None, primary_key=True)
    Tgl: str
    Jmlh: str
    Lunas: bool
    ID: int
    Bulan:date
    IDGajiDetail:int
    IDBill:int
    Ket: str