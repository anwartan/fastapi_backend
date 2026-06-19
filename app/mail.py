from fastapi_mail import FastMail,MessageSchema,ConnectionConfig,MessageType
import os
from typing import Annotated
from fastapi import Depends
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),  # Use an App Password, not your master password  # type: ignore
    MAIL_FROM=os.getenv("MAIL_FROM", ""),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_HOST", ""),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)
def get_mail():
    print(conf)
    return FastMail(conf)

Mail=Annotated[FastMail,Depends(get_mail)]