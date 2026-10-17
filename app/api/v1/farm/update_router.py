
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from sqlmodel import select


from app.api.v1.kafe.auto_update_router import APK_DIR, APK_FILENAME
from app.database import SessionDB1
from app.model.farm.config_farm import Config


router = APIRouter()
APK_DIR = Path(__file__).resolve().parent.parent.parent.parent / "apk"
APK_FILENAME = "farm.apk"

@router.get("/app_version")
async def get_app_version(request: Request, db: SessionDB1):
    keys =['latest_version', 'latest_build_number','force_update','apk_name']
    config_statement = select(Config).where(Config.Key.in_(keys))
    config = db.exec(config_statement).all()
    for i in config:
        if i.Key == "latest_version":
            LATEST_VERSION = i.Value or ""
        elif i.Key == "latest_build_number":
            BUILD_NUMBER = int(i.Value or 0)
        elif i.Key == "force_update":
            FORCE_UPDATE = bool(int(i.Value or 0))
        elif i.Key == "apk_name":
            FILE_NAME = i.Value or ""
    
    apk_path = APK_DIR / FILE_NAME
    if not apk_path.exists():
        raise HTTPException(status_code=404, detail="APK rilis terbuka belum diupload ke server")
    
    download_url = str(request.url_for("download_farm_apk"))
    
    return {
        "data": {
            "latest_version": LATEST_VERSION,
            "latest_build_number": BUILD_NUMBER,
            "apk_url": download_url,
            "force_update": FORCE_UPDATE,
        }
    }
@router.get("/download", name="download_farm_apk")
async def download_apk():
    apk_path = APK_DIR / APK_FILENAME
    if not apk_path.exists():
        raise HTTPException(status_code=404, detail="file apk tidak ditemukan di server")
    
    return FileResponse(
        path=apk_path,
        media_type="application/vnd.android.package-archive",
        filename="farm.apk",
    )