from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.farm import ayamklr_router, ayammini_router, pickuptelur_router, report_router
from app.database import test_database_connection
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.kafe.jenisstock_router import router as jenisstock_router
from app.api.v1.kafe.belanja_router import router as belanja_router
from app.api.v1.kafe.orderstock_router import router as order_router
from app.api.v1.kafe.bborder import router as bborder_router
from app.api.v1.kafe.image_router import router as image_router
from app.api.v1.kafe.auth_router import router as auth_router
from app.api.v1.kafe.mail_router import router as mail_router

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.on_event("startup")
def startup_event():
    logging.info("Aplikasi dimulai...")
    test_database_connection()
    for route in app.routes:
        logging.info(f"Route terdaftar: {route.path}")
    
     

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


base_kafe_url = base_url + "/kafe"
app.include_router(jenisstock_router, prefix=base_kafe_url+"/jenisstock", tags=["JenisStock"])
app.include_router(belanja_router, prefix=base_kafe_url+"/belanja", tags=["Belanja"])
app.include_router(order_router, prefix=base_kafe_url+"/orderstock", tags=["Orderstock"])
app.include_router(bborder_router, prefix=base_kafe_url+"/bborder", tags=["BBOrder"]) 
app.include_router(auth_router, prefix=base_kafe_url+"/auth", tags=["Auth"])
app.include_router(image_router,prefix=base_kafe_url+"/image",tags=["image"])

base_farm_url = base_url + "/farm"

app.include_router(ayammini_router.router, prefix=base_farm_url+"/ayammini", tags=["Ayammini"])
app.include_router(ayamklr_router.router, prefix=base_farm_url+"/ayamklr", tags=["Ayamklr"])
app.include_router(report_router.router, prefix=base_farm_url+"/report", tags=["Report"])
app.include_router(pickuptelur_router.router, prefix=base_farm_url+"/pickuptelur", tags=["Pickuptelur"])
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