
import firebase_admin
from firebase_admin import credentials, messaging

cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred)


class FirebaseService:

    @staticmethod
    def send_notification(token: str, title: str, body: str):
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
                
            ),
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    channel_id="high_importance_channel",
                    sound="default",
                ),
            ),
            token=token,
        )
        response = messaging.send(message)
        return response

    @staticmethod
    def send_mass_notification(tokens: list, title: str, body: str):
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            tokens=tokens
        )
        response = messaging.send_multicast(message)
        return response
    
    @staticmethod
    def send_to_topic( topic: str, title: str, body: str, data: dict |None = None):
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            topic=topic,
            data=data,
            android=messaging.AndroidConfig(
                priority="high",
            )
        )
        messaging.send(message)
    # @staticmethod
    # def subscribe_to_topic(token: str, topic: str):
    #     response = messaging.subscribe_to_topic([token], topic)
    #     return response


