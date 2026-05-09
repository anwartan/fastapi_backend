import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Ayamklr(SQLModel, table=True):
    __tablename__ = "ayamklr"

    tgl: datetime.date | None = Field(default=None)
    Bulan: datetime.date | None = Field(default=None)
    ID: int = Field(default=None, primary_key=True, )
    mati: int | None = Field(default=None)
    sakit: int | None = Field(default=None)
    jual: int | None = Field(default=None)
    ket: str | None = Field(default=None)
    Jenisayam: str