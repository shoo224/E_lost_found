# email.py - Send emails via SMTP or AWS SES
# Used for OTP, match notifications, and claim updates

import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body_text: str, body_html: Optional[str] = None) -> bool:
    """
    Send email. Prefer AWS SES if credentials set; fallback to SMTP.
    Returns True on success, False on failure.
    """
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY and settings.SES_FROM_EMAIL:
        return _send_via_ses(to, subject, body_text, body_html)
    if settings.SMTP_HOST and settings.SMTP_USER:
        return _send_via_smtp(to, subject, body_text, body_html)
    logger.warning("No email configured (SES or SMTP). Skipping send to %s", to)
    return False


def _send_via_ses(to: str, subject: str, body_text: str, body_html: Optional[str]) -> bool:
    """Send using AWS SES."""
    try:
        import boto3
        from botocore.exceptions import ClientError

        client = boto3.client(
            "ses",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        kwargs = {
            "Source": settings.SES_FROM_EMAIL,
            "Destination": {"ToAddresses": [to]},
            "Message": {
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Text": {"Data": body_text, "Charset": "UTF-8"}},
            },
        }
        if body_html:
            kwargs["Message"]["Body"]["Html"] = {"Data": body_html, "Charset": "UTF-8"}
        client.send_email(**kwargs)
        return True
    except ClientError as e:
        logger.exception("SES send failed: %s", e)
        return False


def _send_via_smtp(to: str, subject: str, body_text: str, body_html: Optional[str]) -> bool:
    """Send using SMTP."""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
        msg["To"] = to
        msg.attach(MIMEText(body_text, "plain"))
        if body_html:
            msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(msg["From"], to, msg.as_string())
        return True
    except Exception as e:
        logger.exception("SMTP send failed: %s", e)
        return False


def send_otp_email(to: str, otp: str) -> bool:
    """Send OTP code to user email."""
    subject = "E Lost & Found - Your OTP"
    body = f"Your verification code is: {otp}. Valid for {settings.OTP_EXPIRE_MINUTES} minutes."
    return send_email(to, subject, body)


def send_match_notification(to: str, item_name: str, found_description: str, claim_url: str) -> bool:
    """Notify lost person that a possible match was found."""
    subject = f"E Lost & Found - Possible match for: {item_name}"
    body = (
        f"A found item might match your lost item: {item_name}.\n\n"
        f"Details: {found_description}\n\n"
        f"Claim here: {claim_url}"
    )
    return send_email(to, subject, body)


def send_claim_approved(to: str, item_name: str) -> bool:
    """Notify user their claim was approved."""
    subject = f"E Lost & Found - Claim approved: {item_name}"
    body = f"Your claim for '{item_name}' has been approved. Please collect the item from the administration."
    return send_email(to, subject, body)


def send_claim_rejected(to: str, item_name: str) -> bool:
    """Notify user their claim was rejected."""
    subject = f"E Lost & Found - Claim update: {item_name}"
    body = f"Your claim for '{item_name}' was not approved. Contact administration for more info."
    return send_email(to, subject, body)
