from pydantic import BaseModel

class PriceListItem(BaseModel):
    id:int|None=None
    tgl:str
    jenis:str
    Jmlh:int
    