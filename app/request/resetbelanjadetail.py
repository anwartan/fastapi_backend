from pydantic import BaseModel
class ResetBelanjaDetailRequest(BaseModel):
    id: int | None = None
    jenis: str
   