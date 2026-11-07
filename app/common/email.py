import os

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=os.getenv("MAIL_PORT"),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS"),
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS"),
    USE_CREDENTIALS=os.getenv("USE_CREDENTIALS"),
    VALIDATE_CERTS=os.getenv("VALIDATE_CERTS")
)

fm = FastMail(conf)

async def send_email(recipients: list, subject: str, body: dict):
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=body,
        subtype=MessageType.plain,
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)
    