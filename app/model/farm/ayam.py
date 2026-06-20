from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Ayam(SQLModel, table=True):
    __tablename__ = "ayam"
    ID: int = Field(default=None, primary_key=True,)
    ID_Mini: int | None = Field(default=None)
    Kandang: str | None = Field(default=None)
    Indexing : int 
    Jenisayam: str
