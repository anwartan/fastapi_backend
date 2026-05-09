from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Price(SQLModel, table=True):
    __tablename__ = "price"
    Jenis: str
    Price: float