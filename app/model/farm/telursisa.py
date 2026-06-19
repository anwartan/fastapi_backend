from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Telursisa(SQLModel, table=True):
    __tablename__ = "telursisa"
    Tgl : str | None = Field(default=None, primary_key=True)
    JmlhKom: int | None = Field(default=None)
    JmlhLap: int | None = Field(default=None)
    JmlhMlm: int | None = Field(default=None)