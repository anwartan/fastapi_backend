from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Unit(SQLModel, table=True):
    __tablename__ = "Unit"
    jenis:str 