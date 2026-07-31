from ast import List
from datetime import date
from email import message
import logging
from pydoc_data import topics
from urllib import response

import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging
from proto import Message

from app.api.v1.kafe.notifikasi_router import notification


class NotificationService:
    def __init__(self):
        if not firebase_admin._apps:
            cred = credentials.Certificate("serviceAccountKeyFarm.json")
            firebase_admin.initialize_app(cred)
    def send_to_token(self, token:str, title: str, body: str, data:Optional[dict] = None):
        message = messaging,Message(notification=messaging.Notification(
            title=title,
            body=body
        ),
        data=data,
        token=token,
        )
        try: 
            response = messaging.send(message)
            return response
        except Exception as e:
            logging.error(f"error mengirim pesan: {e}")
            return None
    def send_multicast(self, tokens : List[str], title:str, body:str):
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            tokens = tokens,
        )
        response = messaging.send_multicast(message)
        return {
            "success_count": response.success_count,
            "failure_count": response.failure_count,
        }
    def send_to_topics(self, title: str, body:str, topic:str = "all_users"):
        message = messaging.Message(
            notification= messaging.Notification(title=title, body=body),
            topic=topic,
            android=messaging.AndroidConfig(
                priority="high",
            ), 
            data={
                "title": title,
                "body":body
            }
        )
        messaging.send(message)