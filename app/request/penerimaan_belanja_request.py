from fastapi import Form
from pydantic import BaseModel

class InputPenerimaanBelanjaRequest(BaseModel):
    id: int
    Jenis: str
    JmlhPenerima: int

    @classmethod
    def as_form(
        cls,
        id: int = Form(...),
        Jenis: str = Form(...),
        JmlhPenerima: int = Form(...),
    ):
        return cls(
            id=id,
            Jenis=Jenis,
            JmlhPenerima=JmlhPenerima,
        )