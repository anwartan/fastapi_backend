from pydantic import BaseModel, field_validator
class Pickuptelurrequest(BaseModel):
    kandang : str
    ikat: int
    papan: int
    butir: int
    tipe: str
    jenis_ayam: str

    @field_validator("kandang")
    def kandang_must_not_empty(cls, k):
        
        return k
    @field_validator("ikat")
    def ikat_must_not_empty(cls, i):
        if i < 1:
            raise ValueError(
                "ikat must bigger than 0"
            )
        return i
    @field_validator("papan")
    def papan_must_not_empty(cls, p):
        if p < 1:
            raise ValueError(
                "papan must bigger than 0"
            )
        return p
    @field_validator("butir")
    def butir_must_not_empty(cls, b):
        if b < 1:
            raise ValueError(
                "butir must bigger than 0"
            )
        return b
    @field_validator("tipe")
    def tipe_must_valid(cls, t):
        if t not in ["P","B"]:
            raise ValueError(
                "tipe should be P and B"
            )
        return t
    @field_validator("jenis_ayam")
    def tipe_must_not_empty(cls, j):
        if j not in ["Layer","Arab"]:
            raise ValueError(
                "jensi_ayam should be layer arab"
            )
        return j

