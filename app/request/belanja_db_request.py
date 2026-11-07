

from pydantic import BaseModel, field_validator

class CreateOrderBelanjaDBItem(BaseModel):
    jenis_stock: str
    qty: float
    harga: float
    divisi: str
    ket: str = ""

   
   
