import aiosmtplib
from email.message import EmailMessage

SMTP_EMAIL = "yourgmail@gmail.com"
SMTP_PASSWORD = "APP_PASSWORD"

async def send_otp_email(to_email: str, otp: str):
    msg = EmailMessage()
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email
    msg["Subject"] = "Kode OTP Reset Password"

    msg.set_content(f"""
Kode OTP kamu: {otp}
Berlaku 5 menit.
""")

    await aiosmtplib.send(
        msg,
        hostname="smtp.gmail.com",
        port=587,
        start_tls=True,
        username=SMTP_EMAIL,
        password=SMTP_PASSWORD
    )