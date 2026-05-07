from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Telurpro(SQLModel, table=True):
    __tablename__ = "telurpro"

    bulan: str | None = Field(default=None)
    Tgl : str | None = Field(default=None)
    ID: int = Field(default=None, primary_key=True, )
    Jmlh: int | None = Field(default=None)
    Persen: float | None = Field(default=None)
    Minggu: int | None = Field(default=None)