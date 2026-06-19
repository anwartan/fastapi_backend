from datetime import datetime
from tkinter.font import Font

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class PerubahanDataAyam(SQLModel, table=True):
    __tablename__ = "perubahandataayam"
    ID: int | None = Field(default=None)
    Tgl : datetime | None = Field(default=None, primary_key=True)
    Bulan: datetime | None = Field(default=None, primary_key=True)
    JmlhAwal: int | None = Field(default=None)
    JmlhSkrg: int | None = Field(default=None)
    Ket: str | None = Field(default=None)
    Bulan1: str | None = Field(default=None)