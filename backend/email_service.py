import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# 🔐 Load environment variables

load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")



def send_email(to_email, subject, body):
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_USER
        msg["To"] = to_email

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)

        return True
    except Exception as e:
        print("Email error:", str(e))
        return False