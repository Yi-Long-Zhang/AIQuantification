"""Data source and notification tests"""

from __future__ import annotations

import pytest

from agent.data import BaseDataSource, register_source, get_source, list_sources
from agent.notify import Notification, broadcast, register_notifier, list_notifiers
from agent.notify.telegram import TelegramNotifier
from agent.notify.webhook import WebhookNotifier


class TestDataSource:
    def test_register_and_list(self):
        class MockSource(BaseDataSource):
            name = "mock"; priority = 1
            async def connect(self): return True
            async def get_klines(self, s, i, p): return []
            async def get_quote(self, s): return {}
        register_source(MockSource())
        assert get_source("mock") is not None
        assert "mock" in list_sources()

    def test_get_missing(self):
        assert get_source("nonexistent") is None


class TestNotification:
    def test_notification_to_dict(self):
        n = Notification(title="Test", message="Hello", level="warning")
        d = n.to_dict()
        assert d["title"] == "Test"
        assert d["level"] == "warning"

    def test_list_notifiers_empty(self):
        assert list_notifiers() == []

    def test_register_notifier(self):
        from agent.notify import _notifiers
        _notifiers.clear()
        register_notifier(TelegramNotifier("token", "chat1"))
        assert "telegram" in list_notifiers()

    @pytest.mark.asyncio
    async def test_broadcast(self):
        from agent.notify import _notifiers
        _notifiers.clear()
        register_notifier(TelegramNotifier("", "chat1"))  # empty token -> False
        n = Notification(title="T", message="M")
        result = await broadcast(n)
        assert "telegram" in result


class TestTelegramNotifier:
    @pytest.mark.asyncio
    async def test_send_no_token(self):
        notifier = TelegramNotifier("", "chat1")
        result = await notifier.send(Notification(title="T", message="M"))
        assert result is False


class TestWebhookNotifier:
    @pytest.mark.asyncio
    async def test_send_no_url(self):
        notifier = WebhookNotifier("")
        result = await notifier.send(Notification(title="T", message="M"))
        assert result is False
