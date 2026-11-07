import os
from collections.abc import Sequence
from io import BytesIO

import qrcode
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from starlette.datastructures import Headers, UploadFile

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=os.getenv("MAIL_PORT"),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS"),
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS"),
    USE_CREDENTIALS=os.getenv("USE_CREDENTIALS"),
    VALIDATE_CERTS=os.getenv("VALIDATE_CERTS"),
)

fm = FastMail(conf)


async def send_email(
    recipients: list[str],
    subject: str,
    body: str,
    attachments: Sequence[UploadFile] | None = None,
):
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=body,
        attachments=list(attachments or ()),
        subtype=MessageType.plain,
    )

    fm = FastMail(conf)
    await fm.send_message(message)


def create_text_attachment(filename: str, content: str) -> UploadFile:
    return UploadFile(
        filename=filename,
        file=BytesIO(content.encode("utf-8")),
        headers=Headers({"content-type": "text/plain; charset=utf-8"}),
    )


def create_qr_attachment(filename: str, content: str) -> UploadFile:
    image = qrcode.make(content)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return UploadFile(
        filename=filename,
        file=buffer,
        headers=Headers({"content-type": "image/png"}),
    )
