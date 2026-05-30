from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Orderstock(SQLModel, table=True):
    __tablename__ = "OrderStok"
    IDOrder: int = Field(default=None, primary_key=True)
    Tgl: str
    Jenis: str = Field(default=None, primary_key=True)
    Jmlh: int
    JmlhInp: int
    unit: str
    Divisi: str
    Inputer: int
    Ket: str