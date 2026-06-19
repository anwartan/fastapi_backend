from fastapi import Form
from pydantic import BaseModel

class InputPenerimaanOrderstockRequest(BaseModel):
    id: int
    Jenis: str
    JmlhPenerimaan: int

    @classmethod
    def as_form(
        cls,
        id: int = Form(...),
        Jenis: str = Form(...),
        JmlhPenerimaan: int = Form(...),
    ):
        return cls(
            id=id,
            Jenis=Jenis,
            JmlhPenerimaan=JmlhPenerimaan,
        )