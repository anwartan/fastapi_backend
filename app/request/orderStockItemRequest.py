

from pydantic import BaseModel, field_validator

class OrderStockItemRequest(BaseModel):
    id: int|None=None
    jenis_stock: str
    qty: float
    keterangan_jenis_stock:str
    @field_validator('qty')
    def validate_qty(cls, value):
        if value <= 0:
            raise ValueError('Quantity must be greater than zero')
        return value
    @field_validator('jenis_stock')
    def validate_jenis_stock(cls, value):
        if not value:
            raise ValueError('Jenis stock must not be empty')
        return value
    @classmethod
    def validate_divisi(cls, value):
        if not value:
            raise ValueError('Jenis stock must not be empty')
        return value