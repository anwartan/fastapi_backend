from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.auth import get_current_user
from app.model.kafe.member import Member
from app.services.BackUpService import run_backup


router =APIRouter()
@router.get("/")
def backup_database(
    bgTask:BackgroundTasks,
    current_user: Member = Depends(get_current_user)
):

    try:
        bgTask.add_task(run_backup)
        return {
            "message": "Backup proses dilakukan",
            
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )