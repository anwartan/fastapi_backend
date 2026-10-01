from fastapi_mail import FastMail,MessageSchema,ConnectionConfig,MessageType
import os
from typing import Annotated
from fastapi import Depends
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_FARM_USERNAME", ""),
    MAIL_PASSWORD=os.getenv("MAIL_FARM_PASSWORD", ""),  # Use an App Password, not your master password  # type: ignore
    MAIL_FROM=os.getenv("MAIL_FARM_FROM", ""),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_HOST", ""),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)
def get_mail_farm():
    print(conf)
    return FastMail(conf)

MailFarm=Annotated[FastMail,Depends(get_mail_farm)]