import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class TempLangsirMkn(SQLModel, table=True):
    __tablename__ = "TempLangsirMkn"
    id: int = Field(primary_key=True,)
    Tgl: str | None = Field(default=None)
    Dist: int | None = Field(default=None)
    Kandang: int | None = Field(default=None)
    JenisMkn: str | None = Field(default=None)
    Goni: int | None = Field(default=None)
    Kg: int | None = Field(default=None)
    Input: int | None = Field(default=None)
    Editor: int | None = Field(default=None)
    EditVal: int | None = Field(default=None)
    alasan: str | None = Field(default=None)