from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Chating(SQLModel, table=True):
    __tablename__ = "Chating"
    Tgl: str
    Pesan: str
    Orde:str
    ID:int