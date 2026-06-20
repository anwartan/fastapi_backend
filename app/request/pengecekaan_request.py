from pydantic import BaseModel

class PengecekaanRequest(BaseModel):
    id:int|None=None
    jenis:str
    category:str