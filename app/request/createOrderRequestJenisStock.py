
from datetime import datetime

from pydantic import BaseModel,field_validator

from app.request.orderStockItemRequest import OrderStockItemRequest

class CreateOrderStockRequest(BaseModel):
    tgl: str
    # jenis_stock: str
    # qty: int
    ket: str
    category: str
    items:list[OrderStockItemRequest]
    @field_validator('ket')
    def validate_ket(cls, value):
        if not value:
            raise ValueError('Keterangan must not be empty')
        return value
    @field_validator('category')
    def validate_type_category(cls, value):
        if value not in ["OB", "OS"]:
            raise ValueError('Category must be either "OB" or "OS"')
        return value
    @field_validator("tgl")
    def validate_date(cls, value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Tgl must be in the format YYYY-MM-DD")
        return value