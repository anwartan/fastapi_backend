import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.farm import ayamklr_router, ayammini_router, inputprice_router, langsir_router, pickuptelur_router, produksiluar_router, report_router
from app.api.v1.kafe import biometric_router, notifikasi_router, payrol, price_router
from app.database import test_database_connection
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.kafe.testing_router import router as testing_router
from app.api.v1.kafe.jenisstock_router import router as jenisstock_router
from app.api.v1.kafe.belanja_router import router as belanja_router
from app.api.v1.kafe.orderstock_router import router as order_router
from app.api.v1.kafe.bborder import router as bborder_router
from app.api.v1.kafe.image_router import router as image_router
from app.api.v1.kafe.auth_router import router as auth_router
from app.api.v1.kafe.price_router import router as price_router
from app.api.v1.kafe.biometric_router import router as biometric_router
from app.api.v1.kafe.notifikasi_router import router as notifikasi_router
from app.api.v1.kafe.auto_update_router import router as auto_update_router
from app.api.v1.kafe.laporanperitem import router as laporanperitem
from app.database import test_database_connection
from app.ratelimiter import RateLimiterStore
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

app = FastAPI()
limiter = RateLimiterStore(max_tokens=2, refill_rate=2, interval=1.0)
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    Middleware that enforces per-IP rate limiting on every request.
    Adds standard rate limit headers to every response.
    """
    # Identify the client by IP address.
    client_ip = request.client.host
    bucket = limiter.get_bucket(client_ip)

    # Check if the client has tokens available.
    if not bucket.allow_request():
        retry_after = bucket.get_reset_time() - time.time()
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Try again later."},
            headers={
                "Retry-After": str(max(1, int(retry_after))),
                "X-RateLimit-Limit": str(bucket.max_tokens),
                "X-RateLimit-Remaining": str(bucket.get_remaining()),
                "X-RateLimit-Reset": str(int(bucket.get_reset_time())),
            },
        )

    # Request is allowed. Process it and add rate limit headers to the response.
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(bucket.max_tokens)
    response.headers["X-RateLimit-Remaining"] = str(bucket.get_remaining())
    response.headers["X-RateLimit-Reset"] = str(int(bucket.get_reset_time()))
    return response
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

@app.get("/data")
async def get_data():
    return {"data": "Some important information"}


base_kafe_url = base_url + "/kafe"
app.include_router(jenisstock_router, prefix=base_kafe_url+"/jenisstock", tags=["JenisStock"])
app.include_router(belanja_router, prefix=base_kafe_url+"/belanja", tags=["Belanja"])
app.include_router(order_router, prefix=base_kafe_url+"/orderstock", tags=["Orderstock"])
app.include_router(bborder_router, prefix=base_kafe_url+"/bborder", tags=["BBOrder"])
app.include_router(auth_router, prefix=base_kafe_url+"/auth", tags=["Auth"])
app.include_router(image_router, prefix=base_kafe_url+"/image", tags=["image"])
app.include_router(price_router, prefix=base_kafe_url+"/pricedetail", tags=["price"])
app.include_router(biometric_router,prefix=base_kafe_url+"/biometric",tags=["biometric"])
app.include_router(notifikasi_router,prefix=base_kafe_url+"/notifikasi",tags=["notifikasi"])
app.include_router(auto_update_router,prefix=base_kafe_url+"/update",tags=["update"])
app.include_router(laporanperitem, prefix=base_kafe_url+"/laporanperitem", tags=["laporanperitem"])
app.include_router(payrol.router, prefix=base_kafe_url+"/payrol", tags=["payrol"])
app.include_router(testing_router,prefix=base_kafe_url+"/testing",tags=['testing'])
base_farm_url = base_url + "/farm"
app.include_router(ayammini_router.router, prefix=base_farm_url+"/ayammini", tags=["Ayammini"])
app.include_router(ayamklr_router.router, prefix=base_farm_url+"/ayamklr", tags=["Ayamklr"])
app.include_router(report_router.router, prefix=base_farm_url+"/report", tags=["Report"])
app.include_router(pickuptelur_router.router, prefix=base_farm_url+"/pickuptelur", tags=["Pickuptelur"])
app.include_router(produksiluar_router.router, prefix=base_farm_url+"/produksiluar", tags=["Produksiluar"])
app.include_router(inputprice_router.router, prefix=base_farm_url+"/inputprice", tags=["Inputprice"])
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
