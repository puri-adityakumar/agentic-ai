import os
import smtplib
from email.message import EmailMessage # built-in to python


EMAIL_ADDRESS=os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD=os.environ.get("EMAIL_PASSWORD")
EMAIL_HOST=os.environ.get("EMAIL_HOST") or "smtp.gmail.com"
EMAIL_PORT=os.environ.get("EMAIL_PORT") or 465


def send_mail(subject: str = "No subject provided", content:str = "No message provided", to_email:str=EMAIL_ADDRESS, from_email:str=EMAIL_ADDRESS):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(content)
    with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        return smtp.send_message(msg)