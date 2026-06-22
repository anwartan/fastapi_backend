from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Harga(SQLModel, table=True):
    __tablename__ = "harga"
    Tgl: str = Field(default=None, primary_key=True,)
    Harga: float | None = Field(default=None)
    Ket: str | None = Field(default=None)
    Jenis: str |None = Field(default = None)
