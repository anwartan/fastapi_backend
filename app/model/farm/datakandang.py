from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Datakandang(SQLModel, table=True):
    __tablename__ = "datakandang"

    ID: int = Field(default=None, primary_key=True, )
    Kandang: str | None = Field(default=None)
    kapasitas: int | None = Field(default=None)