from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Jnsstock(SQLModel, table=True):
    __tablename__ = "JnsStok"
    ID: int = Field(default=None, primary_key=True)
    Jenis: str
    Unit: str
    Jmlh: int
    Unit1: str
    Aktif: bool