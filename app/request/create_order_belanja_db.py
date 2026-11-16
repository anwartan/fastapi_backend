from datetime import datetime
from venv import create

from pydantic import BaseModel,field_validator

from app.request.belanja_db_request import CreateOrderBelanjaDBItem

class CreateOrderBelanjaDBRequest(BaseModel):
    tgl: str
    total: float
    ket: str
    category: str = "DB"
    items:list[CreateOrderBelanjaDBItem]
    