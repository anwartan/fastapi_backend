from pydantic import BaseModel, field_validator

class BelanjaanDetailItemRequest(BaseModel):
    id: int|None=None
    jenis: str
    qty: int
    harga: int
    ket: str
    