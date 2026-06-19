from dataclasses import field
from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class InpAyammini(SQLModel, table=True):
    __tablename__ = "inpayamini"

    ID: int = Field(default=None, primary_key=True, )
    Tgl: str | None = Field(default=None)
    JmlhMkn: int | None = Field(default=None)
    JmlhKlr: int | None = Field(default=None)
    Ket: str | None = Field(default=None)
    JmlhJual: int | None = Field(default=None)
    Makanan2: str |None = Field(default=None)
    Jmlh2: int | None = Field(default=None)