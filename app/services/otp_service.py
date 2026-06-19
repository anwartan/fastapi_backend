import random
from datetime import datetime, timedelta

# sementara pakai memory dulu (nanti bisa DB)
otp_store = {}

def generate_otp():
    return str(random.randint(100000, 999999))

def save_otp(email: str, otp: str):
    otp_store[email] = {
        "otp": otp,
        "expire": datetime.now() + timedelta(minutes=5)
    }

def verify_otp(email: str, otp: str):
    data = otp_store.get(email)

    if not data:
        return False

    if datetime.now() > data["expire"]:
        return False

    return data["otp"] == otp