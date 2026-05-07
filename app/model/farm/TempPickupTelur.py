from dataclasses import field
from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class TempPickUpTelur(SQLModel, table=True):
    __tablename__ = "TempPickTelur"
    id: int = Field(primary_key=True, default=None)
    Tgl : str 
    Dist : int 
    Kandang: str 
    Ikat: int 
    Ppn: int 
    Butir: int 
    Tipe : str 
    Jenisayam: str 
    Input: str 

    