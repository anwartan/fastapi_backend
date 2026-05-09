from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Bborder(SQLModel, table=True):
    __tablename__ = "BBOrder"
    Tgl: str
    IDOrder: int = Field(default=None, primary_key=True)
    Total: float
    Aktif: bool
    Inputer: int
    Category: str
    Checked: bool
    ID_Check: int
    Ket: str
   