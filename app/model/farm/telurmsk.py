from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Telurmsk(SQLModel, table=True):
    __tablename__ = "telurmsk"

    Tgl : datetime.date | None = Field(default=None)
    Nama: str | None = Field(default=None)
    Jmlh: int | None = Field(default=None)
    JenisTelur: str | None = Field(default=None)