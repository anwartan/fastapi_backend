import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Ayammini(SQLModel, table=True):
    __tablename__ = "ayammini"

    ID_kcl : int | None = Field(default=None)
    ID: int = Field(primary_key=True,)
    Tgl: str | None = Field(default=None)
    Jenis: str |None = Field(default=None)
    Jmlh: int| None= Field(default=None)
    Ket: str |None = Field(default=None)
    JenisAyam: str|None = Field(default=None)
    Kelas: str |None = Field(default=None)
    PosAyamMini: int | None= Field(default=None)