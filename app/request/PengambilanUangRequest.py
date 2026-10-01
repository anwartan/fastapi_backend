from pydantic import BaseModel


class PengambilanUangRequest(BaseModel):
    id: int
    PengambilanUang: int