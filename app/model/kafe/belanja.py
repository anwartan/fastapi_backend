from click import File
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Belanja(SQLModel, table=True):
    __tablename__ = "Belanja" # type: ignore
    ID: int = Field(default=None, primary_key=True)
    Jenis: str=Field(default=None,primary_key=True)
    JmlhOrder: int=Field(default=None)
    JmlhPenerima: int=Field(default=None)
    ID_Penerima: int=Field(default=None)
    Jmlh: int=Field(default=None)
    ID_Belanja: int=Field(default=None)
    Unit: str=Field(default=None)
    Price: float=Field(default=None)
    Divisi: str=Field(default=None)
    ket: str=Field(default=None)
    Checked: bool=Field(default=None)
    ID_UserBelanja:int=Field(default=None)
    
    @staticmethod
    def subject_type():
        return "OB"
