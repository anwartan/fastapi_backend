from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer

class Ayamvaksin(SQLModel, table=True):
    __tablename__ = "ayamvaksin"
    ID_Kcl: int = Field(default=None)
    ID_Mini: int | None = Field(default=None)
    ID_Bsr: int | None = Field(default=None)
    Tgl: str | None = Field(default=None)
    Vaksin: str | None = Field(default=None)
    Obat: str | None = Field(default=None)
    BiayaVaksin: int | None = Field(default=None)
    BiayaObat: int | None = Field(default=None)
    PerVaksin: str | None = Field(default=None)
    KetUmum: str | None = Field(default=None)
    PerObat: str | None = Field(default=None)

    __mapper_args__ = {
        "primary_key": ["ID_Kcl", "ID_Mini", "ID_Bsr", "Tgl"]
    }
