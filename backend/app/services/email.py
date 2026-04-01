# email.py - Send emails via SMTP or AWS SES
# Used for OTP, match notifications, and claim updates

import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body_text: str, body_html: Optional[str] = None) -> bool:
    """
    Send email with the following priority:
    1. SendGrid (if SENDGRID_API_KEY set)
    2. AWS SES (if AWS credentials set)
    3. SMTP (if SMTP settings set)

    Returns True on success, False on failure.
    """
    if settings.SENDGRID_API_KEY:
        return _send_via_sendgrid(to, subject, body_text, body_html)
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY and settings.SES_FROM_EMAIL:
        return _send_via_ses(to, subject, body_text, body_html)
    if settings.SMTP_HOST and settings.SMTP_USER:
        return _send_via_smtp(to, subject, body_text, body_html)
    logger.warning("No email configured (SendGrid, SES, or SMTP). Skipping send to %s", to)
    return False


def _send_via_sendgrid(to: str, subject: str, body_text: str, body_html: Optional[str]) -> bool:
    """Send using SendGrid API."""
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        from_address = settings.SENDGRID_FROM or settings.SMTP_FROM or settings.SES_FROM_EMAIL
        if not from_address:
            logger.error("SendGrid from address is not configured")
            return False

        message = Mail(
            from_email=from_address,
            to_emails=to,
            subject=subject,
            plain_text_content=body_text,
            html_content=body_html,
        )
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        if response.status_code in (200, 202):
            return True
        logger.error("SendGrid send failed: status=%s, body=%s", response.status_code, response.body)
        return False
    except Exception as e:
        logger.exception("SendGrid send failed: %s", e)
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
