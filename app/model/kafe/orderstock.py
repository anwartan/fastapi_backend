from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Orderstock(SQLModel, table=True):
    __tablename__ = "OrderStok" # type: ignore
    ID_OrderStock: int=Field(default=None)
    IDOrder: int = Field(default=None, primary_key=True)
    Tgl: str
    Jenis: str = Field(default=None, primary_key=True)
    Jmlh: float
    JmlhInp: float
    unit: str
    Divisi: str
    Inputer: int
    Ket: str
    Checked:int
    ID_Penerimaan:int 
    @staticmethod
    def subject_type():
        return "OS"
        