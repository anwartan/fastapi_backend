from datetime import datetime

from pydantic import BaseModel, field_validator

class BelanjaanDetailItemRequest(BaseModel):
    id: int|None=None
    tgl:datetime
    jenis: str
    qty: float
    harga: int
    ket: str
    