from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import requests
from app.core.config import SENDER_EMAIL, SENDER_PASSWORD, BREVO_URL, BREVO_API_KEY, BREVO_SENDER_EMAIL

# def send_otp_email(receiver_email: str, otp: str):
#     try:
#         message = MIMEMultipart()
#         message["From"] = SENDER_EMAIL
#         message["To"] = receiver_email
#         message["Subject"] = "รหัส OTP สำหรับตั้งรหัสผ่านใหม่"

#         body = f"""
#         <html>
#             <body>
#                 <h2>รีเซ็ตรหัสผ่าน</h2>
#                 <p>รหัส OTP 6 หลักของคุณคือ: <b style="font-size: 24px; color: #4CAF50;">{otp}</b></p>
#                 <p>รหัสนี้จะหมดอายุภายใน 5 นาที หากคุณไม่ได้เป็นผู้ขอรีเซ็ตรหัสผ่าน โปรดเพิกเฉยต่ออีเมลฉบับนี้</p>
#             </body>
#         </html>
#         """
#         message.attach(MIMEText(body, 'html'))

#         server = smtplib.SMTP("smtp.gmail.com", 587)
#         server.starttls()
#         server.login(SENDER_EMAIL, SENDER_PASSWORD)
#         server.send_message(message)
#         server.quit()
#         print(f"ส่งอีเมล OTP ไปที่ {receiver_email} สำเร็จ!")
#         return True

#     except Exception as e:
#         print(f"เกิดข้อผิดพลาดในการส่งอีเมล OTP: {e}")
#         return False

def send_otp_email(receiver_email: str, otp: str):
    # payload = {
    #     "sender": {"email": BREVO_SENDER_EMAIL},
    #     "to": [{"email": receiver_email}],
    #     "subject": "รหัส OTP สำหรับรีเซ็ตรหัสผ่าน",
    #     "htmlContent": f"""
    #         <h2>รีเซ็ตรหัสผ่าน</h2>
    #         <p>OTP ของคุณคือ:</p>
    #         <h1 style="letter-spacing:4px;">{otp}</h1>
    #         <p>รหัสนี้จะหมดอายุภายใน 5 นาที</p>
    #     """
    # }

    # headers = {
    #     "accept": "application/json",
    #     "api-key": BREVO_API_KEY,
    #     "content-type": "application/json"
    # }
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, Helvetica, sans-serif; background-color: #f9f9f9;">
        
        <div style="max-width: 500px; margin: 40px auto; background-color: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #FF9800; margin: 0; font-size: 28px; font-weight: 800;">Find My Food </h1>
            </div>
            
            <div style="color: #333333; font-size: 16px; line-height: 1.6;">
                <h2 style="color: #2c3e50; font-size: 20px; text-align: center; margin-bottom: 20px;">คำขอรีเซ็ตรหัสผ่าน</h2>
                <p>สวัสดีครับ,</p>
                <p>เราได้รับคำขอให้รีเซ็ตรหัสผ่านสำหรับบัญชี <strong>Find My Food</strong> ของคุณ โปรดใช้รหัส OTP ด้านล่างนี้เพื่อยืนยันตัวตน:</p>
                
                <div style="background-color: #FFF3E0; border: 2px dashed #FF9800; border-radius: 8px; padding: 25px; text-align: center; margin: 30px 0;">
                    <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #E65100;">{otp}</span>
                </div>
                
                <p style="text-align: center; color: #e74c3c; font-size: 14px; font-weight: bold;">
                    รหัสนี้จะหมดอายุภายใน 15 นาที
                </p>
                <hr style="border: none; border-top: 1px solid #eeeeee; margin: 30px 0;">
                <p style="font-size: 12px; color: #888888; text-align: center; line-height: 1.5;">
                    หากคุณไม่ได้เป็นผู้ขอรีเซ็ตรหัสผ่าน โปรดเพิกเฉยต่ออีเมลฉบับนี้<br>
                    เพื่อความปลอดภัย <strong>ห้ามเปิดเผยรหัสนี้แก่ผู้อื่นโดยเด็ดขาด</strong>
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    payload = {
        "sender": {"name": "Find My Food", "email": BREVO_SENDER_EMAIL}, 
        "replyTo": {"email": BREVO_SENDER_EMAIL, "name": "Find My Food Support"},
        "to": [{"email": receiver_email}],
        "subject": "[Find My Food] รหัส OTP สำหรับรีเซ็ตรหัสผ่าน", 
        "htmlContent": html_template,
        "textContent": f"สวัสดีครับ\n\nรหัส OTP สำหรับรีเซ็ตรหัสผ่านบัญชี Find My Food ของคุณคือ: {otp}\nรหัสนี้จะหมดอายุภายใน 5 นาที\n\nหากไม่ได้ทำรายการ โปรดเพิกเฉยต่ออีเมลฉบับนี้",
        "headers": {
            "X-Mailin-custom": "OTP-Reset"
        }
    }

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    try:
        response = requests.post(BREVO_URL, json=payload, headers=headers, timeout=10)
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)
        return response.status_code in (200, 201, 202)
    except Exception as e:
        print("Brevo Error:", e)
        return False