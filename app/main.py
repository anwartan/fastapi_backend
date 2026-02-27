from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.v1 import ayam
from app.database import test_database_connection
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
app = FastAPI()
base_url = "/api/v1"

@app.on_event("startup")
def startup_event():
    logging.info("Aplikasi dimulai...")
    test_database_connection()
    for route in app.routes:
        logging.info(f"Route terdaftar: {route.path}")
    

app.include_router(ayam.router, prefix=base_url+"/ayam", tags=["Ayam"])
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logging.error(f"Terjadi kesalahan: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Terjadi kesalahan pada server. Silakan coba lagi nanti."},
    )

@app.get("/")
def root():
    return {"message": "API is running"}