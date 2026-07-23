"""
Telegram Notifier

Sends trading signals and alerts via Telegram Bot API.
Uses httpx for async HTTP calls.
"""

from __future__ import annotations

import logging

import httpx

from agent.notify import BaseNotifier, Notification

logger = logging.getLogger(__name__)


class TelegramNotifier(BaseNotifier):
    """Send notifications via Telegram Bot."""

    name = "telegram"

    def __init__(self, bot_token: str, chat_id: str):
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._client: httpx.AsyncClient | None = None

    async def send(self, notification: Notification) -> bool:
        if not self._bot_token or not self._chat_id:
            return False

        client = self._client or httpx.AsyncClient(timeout=10)
        emoji = {"info": "ℹ️", "warning": "⚠️", "alert": "🚨", "success": "✅"}

        text = f"{emoji.get(notification.level, '📌')} *{notification.title}*\n"
        text += f"`{notification.source}`\n\n"
        text += notification.message

        try:
            url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
            resp = await client.post(url, json={
                "chat_id": self._chat_id,
                "text": text,
                "parse_mode": "Markdown",
            })
            success = resp.status_code == 200
            if success:
                logger.info(f"Telegram sent: {notification.title}")
            else:
                logger.warning(f"Telegram send failed: {resp.status_code} {resp.text}")
            return success
        except Exception as e:
            logger.error(f"Telegram error: {e}")
            return False
