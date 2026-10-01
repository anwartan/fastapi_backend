from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from services.BackUpService import run_backup as main


app = FastAPI()

scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def startup_event():
    scheduler.add_job(
        main,
        "cron",
        hour=15,
        minute=0,
        id="daily_backup",
        replace_existing=True
    )

    scheduler.start()

    print("Scheduler backup aktif")
    print("Backup otomatis setiap hari pukul 15:00")


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()