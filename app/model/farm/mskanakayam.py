from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Mskanakayam(SQLModel, table=True):
    __tablename__ = "mskanakayam"
    ID: int = Field(default=None, primary_key=True,)
    TglMsk:  str | None = Field(default=None)
    Jmlh : int | None = Field(default=None)
    Bonus : int | None = Field(default=None)
    Jenis : str | None = Field(default=None)
    Ket : str | None = Field(default=None)
    Bibit : str | None = Field(default=None)
    PosAyamKcl : bool | None = Field(default=None)
    Kelas : str | None = Field(default=None)
    PosAyamMini : bool | None = Field(default=None)
    PosAyamBsr : bool | None = Field(default=None)
    JenisAyam : str | None = Field(default=None)