import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Templangsirmakan(SQLModel, table=True):
    __tablename__ = "templangsirmakan"
    ID: int = Field(primary_key=True,)
    Tgl: datetime.date | None = Field(default=None)
    Dist: int | None = Field(default=None)
    Kandang: str | None = Field(default=None)
    Ikat: int | None = Field(default=None)
    Ppn: int | None = Field(default=None)
    Butir: int | None = Field(default=None)
    Tipe: str | None = Field(default=None)
    Jenisayam: str | None = Field(default=None)
    Input: str | None = Field(default=None)