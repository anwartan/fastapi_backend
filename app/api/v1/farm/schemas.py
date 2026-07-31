from pydantic import BaseModel
from datetime import date

class HargaInput(BaseModel):
    tanggal: date
    jenis: str
    harga: int