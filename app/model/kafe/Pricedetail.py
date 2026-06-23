from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Pricedetail(SQLModel, table=True):
    __tablename__ = "pricedetail"
    ID_PriceDetail:int = Field(default=None, primary_key=True)
    Tgl: str
    Jenis: str
    Jmlh: int
    Inputer: int