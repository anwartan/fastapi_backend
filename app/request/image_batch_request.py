import base64
import mimetypes
from pydantic import BaseModel
class ImageBatchRequest(BaseModel):
    category: str
    ids: list[int]


