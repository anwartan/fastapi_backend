
from sqlmodel import Field, SQLModel

from datetime import date

class member(SQLModel, table=True):
    __tablename__ = "member"
    ID:int = Field(default=None, primary_key=True)
    Nama: str
    alamat: str
    TglLahir: str
    Ket: str
    Tingkat: str
    Active:int
    Username: str
    PW: str
    Divisi:str
    Status:str
    Tgl:date
    Email:str
    VerifyDate:date
