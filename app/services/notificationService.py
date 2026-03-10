import firebase_admin
from firebase_admin import credentials, messaging
from firebase_admin.messaging import UnregisteredError
from sqlmodel import Session, select, update, func
from app.core import datetimezone
from app.services import userStockService
from app.models.userModel import MasUserModel
from app.models.notificationModel import TrnNotificationModel

cred = credentials.Certificate("firebase-adminsdk.json")
firebase_admin.initialize_app(cred)

def send_expired_push_notification(fcm_token: str, title: str, body: str):
    if not fcm_token:
        print("Error: ไม่มี FCM Token ไม่สามารถส่งแจ้งเตือนได้")
        raise

    try:
        message = messaging.Message(
        notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=fcm_token,
        )
        response = messaging.send(message)
        return True
    except UnregisteredError:
        print("Error: ไม่มี FCM Token ไม่สามารถส่งแจ้งเตือนได้")
        raise UnregisteredError("No FCM Token")

    except Exception as ex:
        print(f"Error: แจ้งเตือนล้มเหลว: {str(ex)}")
        return False
    
def save_notification_message(user_id: int, title: str, body: str, db: Session):
    new_notification = TrnNotificationModel(
        user_id=user_id, 
        title=title, 
        body=body,
        read_date=None,
        is_read=False
    )

    db.add(new_notification)
    db.flush()
    db.refresh(new_notification)
    return new_notification

def send_expire_push_notification_process(db: Session):
    try:
        users = userStockService.check_item_expire_date(db)
        for u in users:
            user_id = u['user_id']
            username = u['username']
            fcm_token = u['fcm_token']

            title = f"🚨 อย่าปล่อยให้ของอร่อยต้องเสียเปล่า!"
            body = f"คุณ {username} มีของใกล้หมดอายุ รีบเอามาทำเมนูอร่อยๆ เพื่อเซฟเงินและลดขยะกันเถอะ ✨"
            print(f"แจ้งเตือนหา: {username} -> {title} -> {body}")

            try:
                save_notification_message(user_id, title, body, db)
                if fcm_token:
                    try:
                        send_expired_push_notification(fcm_token, title, body)
                    except UnregisteredError:
                        print(f"กำลังล้าง Token ของ User ID: {username} ออกจากระบบ...")
                        user_update = db.get(MasUserModel, user_id)
                        if user_update:
                            user_update.fcm_token = None
                
                db.commit()
                print(f"แจ้งเตือน {username} เสร็จสมบูรณ์")

            except Exception as ex:
                print(f"error ของ {username}: {str(ex)}")
                db.rollback()
            
    except Exception as ex:
        print(f"error: {str(ex)}")
        db.rollback()
        raise

def get_unread_notification_count(user_id: int, db: Session):
    notification_count = db.exec(
        select(
            func.count(TrnNotificationModel.notification_id)
        ).where(
            TrnNotificationModel.user_id == user_id,
            TrnNotificationModel.is_read == False
        )
    ).first()
    
    return notification_count

def get_all_notifications(user_id: int, db: Session):
    notifications = db.exec(
        select(
            TrnNotificationModel
        ).where(
            TrnNotificationModel.user_id == user_id
        )
    ).all()
    
    return notifications

def read_notification(user_id: int, db: Session):
    try:
        db.exec(
            update(TrnNotificationModel)
            .where(
                TrnNotificationModel.user_id == user_id,
                TrnNotificationModel.is_read == False
            )
            .values(
                is_read=True,
                read_date=datetimezone.get_thai_now()
            )
        )
        db.commit()
    except Exception as ex:
        print(f"error: {str(ex)}")
        db.rollback()
        raise