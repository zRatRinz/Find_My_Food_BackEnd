from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from app.core.config import SENDER_EMAIL, SENDER_PASSWORD

def send_otp_email(receiver_email: str, otp: str):
    try:
        message = MIMEMultipart()
        message["From"] = SENDER_EMAIL
        message["To"] = receiver_email
        message["Subject"] = "รหัส OTP สำหรับตั้งรหัสผ่านใหม่"

        body = f"""
        <html>
            <body>
                <h2>รีเซ็ตรหัสผ่าน</h2>
                <p>รหัส OTP 6 หลักของคุณคือ: <b style="font-size: 24px; color: #4CAF50;">{otp}</b></p>
                <p>รหัสนี้จะหมดอายุภายใน 5 นาที หากคุณไม่ได้เป็นผู้ขอรีเซ็ตรหัสผ่าน โปรดเพิกเฉยต่ออีเมลฉบับนี้</p>
            </body>
        </html>
        """
        message.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(message)
        server.quit()
        print(f"ส่งอีเมล OTP ไปที่ {receiver_email} สำเร็จ!")
        return True

    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการส่งอีเมล OTP: {e}")
        return False