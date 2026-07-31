from pydantic import BaseModel


class UpdateStockPengecekaan(BaseModel):
    id:int
    jenis:str
    jmlhinput:float
    jmlhpengiriman:float