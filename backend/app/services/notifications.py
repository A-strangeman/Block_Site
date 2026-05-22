import asyncio

import httpx
from typing import cast
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.core.config import settings
from app.models.approval_request import ApprovalRequest
from app.models.friend import Friend
from app.models.user import User


async def _send_email(*, to_email: str, subject: str, text: str) -> None:
    if not settings.sendgrid_api_key or not settings.sendgrid_from_email:
        return
    message = Mail(from_email=settings.sendgrid_from_email, to_emails=to_email, subject=subject, plain_text_content=text)
    client = SendGridAPIClient(settings.sendgrid_api_key)
    await asyncio.to_thread(client.send, message)


async def _send_sms(*, to_number: str, text: str) -> None:
    if not all([settings.twilio_account_sid, settings.twilio_auth_token, settings.twilio_from_number]):
        return
    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
    auth = cast(tuple[str, str], (settings.twilio_account_sid, settings.twilio_auth_token))
    payload = {"From": settings.twilio_from_number, "To": to_number, "Body": text}
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(url, data=payload, auth=auth)


async def notify_friend_about_block(*, db, user: User, friend: Friend, domain: str) -> None:
    message = f"{user.email.split('@')[0].title()} attempted to open {domain} at a blocked time."
    if friend.notification_channel == "sms" and friend.phone:
        await _send_sms(to_number=friend.phone, text=message)
        return
    if friend.email:
        await _send_email(to_email=friend.email, subject="FocusGuard block alert", text=message)


async def send_approval_request_notification(*, db, user: User, friend: Friend, request: ApprovalRequest) -> None:
    approval_url = f"https://focusguard.app/approve?token={request.token}"
    message = f"Approve access for {user.email}. Use this link: {approval_url}"
    if friend.notification_channel == "sms" and friend.phone:
        await _send_sms(to_number=friend.phone, text=message)
        return
    if friend.email:
        await _send_email(to_email=friend.email, subject="FocusGuard approval request", text=message)
