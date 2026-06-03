import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from dotenv import load_dotenv


class EmailConfigError(Exception):
    pass


class EmailSendError(Exception):
    pass


@dataclass(frozen=True)
class EmailConfig:
    host: str | None
    port: int
    username: str | None
    password: str | None
    sender: str | None
    use_tls: bool

    @classmethod
    def from_env(cls) -> "EmailConfig":
        load_dotenv()
        port_value = os.getenv("SMTP_PORT", "587")
        try:
            port = int(port_value)
        except ValueError as exc:
            raise EmailConfigError("SMTP_PORT must be an integer") from exc

        return cls(
            host=os.getenv("SMTP_HOST"),
            port=port,
            username=os.getenv("SMTP_USERNAME"),
            password=os.getenv("SMTP_PASSWORD"),
            sender=os.getenv("SMTP_SENDER") or os.getenv("SMTP_USERNAME"),
            use_tls=os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes", "on"},
        )

    def validate(self) -> None:
        if not self.host:
            raise EmailConfigError("SMTP_HOST is required")
        if not self.sender:
            raise EmailConfigError("SMTP_SENDER or SMTP_USERNAME is required")
        if not self.username:
            raise EmailConfigError("SMTP_USERNAME is required")
        if not self.password:
            raise EmailConfigError("SMTP_PASSWORD is required")


def send_email(to_email: str, subject: str, content: str, config: EmailConfig | None = None) -> None:
    email = to_email.strip()
    title = subject.strip()
    body = content.strip()
    if not email:
        raise EmailConfigError("to_email is required")
    if not title:
        raise EmailConfigError("subject is required")
    if not body:
        raise EmailConfigError("content is required")

    email_config = config or EmailConfig.from_env()
    email_config.validate()

    message = EmailMessage()
    message["From"] = email_config.sender
    message["To"] = email
    message["Subject"] = title
    message.set_content(body)

    try:
        with smtplib.SMTP(email_config.host, email_config.port, timeout=30) as smtp:
            if email_config.use_tls:
                smtp.starttls()
            smtp.login(email_config.username, email_config.password)
            smtp.send_message(message)
    except smtplib.SMTPException as exc:
        raise EmailSendError(f"email send failed: {exc}") from exc
