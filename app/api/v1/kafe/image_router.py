from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from app.database import SessionDBKafe
from app.model.kafe.Media import Media
from sqlmodel import select
router = APIRouter()

BASE_DIR = "media/images"



@router.get("/{category}/{id}")
def get_image(
    category: str,
    id: int,
    session: SessionDBKafe
):
    category = category.upper()

    if category not in ["OB", "OS"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid category"
        )

    media = session.exec(
        select(Media).where(
            Media.SubjectId == id,
            Media.SubjectType == category
        )
    ).first()

    if not media:
        raise HTTPException(
            status_code=404,
            detail="Image not found"
        )

    # Jika FilePath menyimpan path lengkap
    file_path = media.FilePath

    # Jika FilePath hanya menyimpan nama file, gunakan ini:
    # file_path = os.path.join(BASE_DIR, media.FileName)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="Physical file not found"
        )

    return FileResponse(file_path)