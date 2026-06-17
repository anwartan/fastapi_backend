import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class TempPickTelur(SQLModel, table=True):
    __tablename__ = "TempPickTelur"
    id: int = Field(primary_key=True,)
    Tgl: str | None = Field(default=None)
    Dist: int | None = Field(default=None)
    Kandang: int | None = Field(default=None)
    Ikat: int | None = Field(default=None)
    Ppn: int | None = Field(default=None)
    Butir: int | None = Field(default=None)
    Tipe: str | None = Field(default=None)
    Jenisayam: str | None = Field(default=None)
    Input: int | None = Field(default=None)