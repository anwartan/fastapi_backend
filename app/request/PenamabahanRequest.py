from pydantic import BaseModel


class PenambahanRequest(BaseModel):
    IDOrder: int
    PenambahanUang: int
