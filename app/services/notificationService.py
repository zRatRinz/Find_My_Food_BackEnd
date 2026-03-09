import firebase_admin
from firebase_admin import credentials, messaging
from sqlmodel import Session
from app.services import userStockService

cred = credentials.Certificate("firebase-adminsdk.json")
firebase_admin.initialize_app(cred)

def send_expired_push_notification(fcm_token, title, body):
    if not fcm_token:
        print("Error: ไม่มี FCM Token ไม่สามารถส่งแจ้งเตือนได้")
        raise

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=fcm_token,
    )
    response = messaging.send(message)
    print(f"แจ้งเตือนสำเร็จ! Message ID: {response}")
    return True

def send_expire_push_notification_process(db: Session):
    try:
        users = userStockService.check_item_expire_date(db)
        for u in users:
            title = f"รายการหมดอายุ ของ {u['username']}"
            body = "กรุณาตรวจสอบรายการหมดอายุ"
            print(f"แจ้งเตือนหา: {u['username']} -> {title} -> {body}")
            send_expired_push_notification(u['fcm_token'], title, body)
    except Exception as ex:
        print(f"error: {str(ex)}")
        raise