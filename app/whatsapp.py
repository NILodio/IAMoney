from fastapi import HTTPException
from .config import settings
import httpx
import logging

logger = logging.getLogger(__name__)


def verify_webhook(mode: str | None, token: str | None, challenge: str | None) -> str:
    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        return challenge or ""
    raise HTTPException(status_code=403, detail="Verification failed")


async def send_whatsapp_text_message(to_phone: str, message: str):
    """
    Real call to WhatsApp Cloud API.
    For local dev you can comment out the HTTP call and just log.
    """
    if settings.WHATSAPP_ACCESS_TOKEN == "change_me":
        logger.info(f"[MOCK] Would send to {to_phone}: {message}")
        return

    url = f"https://graph.facebook.com/v21.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": message},
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
