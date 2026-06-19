from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Telurklr(SQLModel, table=True):
    __tablename__ = "telurklr"
    ID : int | None = Field(default=None, primary_key=True)
    Tgl : str | None = Field(default=None)
    Nama: str | None = Field(default=None)
    Jmlh: int | None = Field(default=None)
    lunas: int | None = Field(default=None)
    Butir: int | None = Field(default=None)
    Ket : str | None = Field(default=None)
    JenisTelur: str | None = Field(default=None)