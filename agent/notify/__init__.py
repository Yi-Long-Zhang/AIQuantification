"""
Notification Subsystem

Base class for multi-channel notifications (Telegram, Email, Webhook).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Notification:
    title: str
    message: str
    level: str = "info"  # info, warning, alert, success
    source: str = "system"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "title": self.title, "message": self.message,
            "level": self.level, "source": self.source,
            "timestamp": self.timestamp,
        }


class BaseNotifier(ABC):
    """Abstract base for notification channels."""

    name: str = "base"

    @abstractmethod
    async def send(self, notification: Notification) -> bool:
        ...


_notifiers: dict[str, BaseNotifier] = {}


def register_notifier(notifier: BaseNotifier) -> None:
    _notifiers[notifier.name] = notifier


async def broadcast(notification: Notification) -> dict[str, bool]:
    """Send notification to all registered channels."""
    results = {}
    for name, notifier in _notifiers.items():
        try:
            results[name] = await notifier.send(notification)
        except Exception as e:
            results[name] = False
    return results


def list_notifiers() -> list[str]:
    return list(_notifiers.keys())
