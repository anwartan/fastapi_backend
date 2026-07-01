from pydantic import BaseModel, field_validator

class BelanjaanDetailItemRequest(BaseModel):
    id: int|None=None
    jenis: str
    qty: float
    harga: int
    ket: str
    