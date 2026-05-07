from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class TempJmlhAyam(SQLModel, table=True):
    __tablename__ = "TempJmlhAyam"
    Tgl : str = Field()
    ID: int = Field(primary_key=True, )
    Kandang: str = Field(default="")
    Indexing: int  = Field(default=0)
    Jmlh: int  = Field(default=0)