"""
Webhook Notifier

Sends JSON notifications to a configurable webhook URL.
Supports DingTalk, WeChat Work, Discord, and custom webhooks.
"""

from __future__ import annotations

import logging

import httpx

from agent.notify import BaseNotifier, Notification

logger = logging.getLogger(__name__)


class WebhookNotifier(BaseNotifier):
    """Send notifications to a generic webhook URL."""

    name = "webhook"

    def __init__(self, url: str, headers: dict | None = None):
        self._url = url
        self._headers = headers or {"Content-Type": "application/json"}

    async def send(self, notification: Notification) -> bool:
        if not self._url:
            return False

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    self._url,
                    json=notification.to_dict(),
                    headers=self._headers,
                )
                success = 200 <= resp.status_code < 300
                if success:
                    logger.info(f"Webhook sent: {notification.title}")
                else:
                    logger.warning(f"Webhook failed: {resp.status_code}")
                return success
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return False
