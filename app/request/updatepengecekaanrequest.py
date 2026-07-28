from pydantic import BaseModel


class UpdatePengecekaan(BaseModel):
    id:int
    jenis:str
    jmlhpenerimaan:float
    jmlh:float