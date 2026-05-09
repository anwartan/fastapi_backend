from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Belanja(SQLModel, table=True):
    __tablename__ = "Belanja"
    ID: int = Field(default=None, primary_key=True)
    Jenis: str=Field(default=None,primary_key=True)
    Jmlh: int=Field(default=None)
    Unit: str=Field(default=None)
    Price: float=Field(default=None)
    Divisi: str=Field(default=None)
    ket: str=Field(default=None)
    Checked: bool=Field(default=None)