from pydantic import BaseModel


class PengirimanOrderStock(BaseModel):
    id:int |None=None
    jenis:str
    jmlhpengiriman:int
