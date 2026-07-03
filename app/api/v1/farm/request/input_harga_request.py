from pydantic import BaseModel
class InputHargaRequest(BaseModel):
    tanggal: str
    jenis: str
    harga: float