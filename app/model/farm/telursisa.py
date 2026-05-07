from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Telursisa(SQLModel, table=True):
    __tablename__ = "telursisa"

    Field1: str | None = Field(default=None)
    Tgl : datetime.date | None = Field(default=None)
    JmlhKom: int | None = Field(default=None)
    JmlhLap: int | None = Field(default=None)
    JmlhMlm: int | None = Field(default=None)