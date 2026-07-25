from pathlib import Path

from fastapi import  APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from sqlmodel import select

from app.database import SessionDBKafe
from app.model.kafe.Config import Config


router=APIRouter()
APK_DIR=Path(__file__).resolve().parent.parent.parent.parent/"apk"
APK_FILENAME="coffeeday.apk"
@router.get("/app_version")
async def get_app_version(request:Request,session:SessionDBKafe):
    keys=["latest_version","latest_bulid_number","force_update","apk_name"]
    query=select(Config).where(Config.Key.in_(keys))
    querys=session.exec(query).all()
    FILE_NAME=""
    LATEST_VERSION=""
    BULID_NUMBER=""
    FORCE_UPDATE=""
    for i in querys:
        if i.Key=="latest_version":
            LATEST_VERSION=i.Value or ""
        elif i.Key=="latest_bulid_number":
            BULID_NUMBER=int(i.Value or 0)
        elif i.Key=="force_update":
            FORCE_UPDATE=bool(int(i.Value or 0))
        elif i.Key=="apk_name":
            FILE_NAME=i.Value or ""
    apk_path=APK_DIR/FILE_NAME 
    if not apk_path.exists():
        raise HTTPException(status_code=404,detail="APK FILE TERBARU BELUM DI UPLOAD")
    download_url=str(request.url_for("download_apk"))
    return{
        "data":{
            "latest_version":"1.0.0",
            "latest_bulid_number":2,
            "apk_url":download_url,
            "force_update":False,
        }
    }

@router.get("/download",name="download_apk")
async def download_apk():
    apk_path=APK_DIR/APK_FILENAME
    if not apk_path.exists():
        raise HTTPException(status_code=404,detail="File Apk tidak di temukan di server")
    return FileResponse(
        path=apk_path,
        media_type="application/vnd.android.package-archive",
        filename="coffe_day.apk"
    )