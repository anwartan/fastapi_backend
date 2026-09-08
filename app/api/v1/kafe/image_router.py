import base64
import mimetypes
import os
import select
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.database import SessionDBKafe
from app.model.kafe.Media import Media
from app.request.image_batch_request import ImageBatchRequest


router=APIRouter()
@router.post("/batch")
def get_images_batch(
    req: ImageBatchRequest,
    session: SessionDBKafe
):
    category = req.category.upper()

    if category not in ["OB", "OS"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid category"
        )

    if not req.ids:
        return {}

    # Hilangkan ID duplikat
    ids = list(set(req.ids))

    medias = session.exec(
        select(Media).where(
            Media.SubjectType == category,
            Media.SubjectId.in_(ids)
        )
    ).all()

    result = {}

    for media in medias:
        file_path = media.FilePath

        if not os.path.exists(file_path):
            continue

        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            mime_type = media.FileType

            if not mime_type:
                mime_type = (
                    mimetypes.guess_type(file_path)[0]
                    or "application/octet-stream"
                )

            result[str(media.SubjectId)] = {
                "fileName": media.FileName,
                "fileType": mime_type,
                "data": base64.b64encode(file_bytes).decode("utf-8"),
            }

        except Exception:
            continue

    return result