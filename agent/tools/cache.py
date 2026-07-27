"""
数据缓存层 — 带 TTL 的内存缓存

用于包装数据获取函数，避免同一参数在短时间内重复请求外部 API。
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

# ── 存储 ─────────────────────────────────────────────────────────────────────

_CACHE_STORE: dict[str, Any] = {}  # key → value
_CACHE_TTL: dict[str, float] = {}  # key → expiry timestamp

# ── 默认 TTL（秒） ───────────────────────────────────────────────────────────

DEFAULT_TTL: dict[str, int] = {
    "klines": 300,      # K 线数据 5 分钟
    "quote": 30,        # 实时报价 30 秒
    "overview": 60,     # 市场概览 1 分钟
    "macro": 3600,      # 宏观数据 1 小时
    "sector": 600,      # 板块数据 10 分钟
    "hk_flow": 300,     # 资金流向 5 分钟
    "hk_valuation": 600,  # 估值数据 10 分钟
    "crypto_orderbook": 10,   # 盘口 10 秒
    "crypto_overview": 60,    # 加密概览 1 分钟
    "crypto_fear_greed": 600, # 恐惧贪婪 10 分钟
    "crypto_funding": 60,     # 资金费率 1 分钟
    "crypto_oi": 60,          # 持仓量 1 分钟
}

T = TypeVar("T")


async def get_or_fetch(
    cache_key: str,
    ttl_type: str,
    fetcher: Callable[[], Coroutine[Any, Any, T]],
) -> T:
    """带 TTL 缓存的异步获取器。

    参数：
        cache_key: 缓存键（通常由函数名 + 参数拼接）
        ttl_type:  TTL 类型名，在 DEFAULT_TTL 中查找对应的过期时间
        fetcher:   异步获取函数（仅在缓存未命中时调用）
    返回：
        数据值（类型由 fetcher 决定）
    """
    now = time.time()
    cached = _CACHE_STORE.get(cache_key)
    expiry = _CACHE_TTL.get(cache_key, 0)

    if cached is not None and expiry > now:
        logger.debug("Cache HIT: %s (ttl=%ds)", cache_key, int(expiry - now))
        return cached  # type: ignore[return-value]

    logger.debug("Cache MISS: %s", cache_key)
    result = await fetcher()
    ttl = DEFAULT_TTL.get(ttl_type, 300)
    _CACHE_STORE[cache_key] = result
    _CACHE_TTL[cache_key] = now + ttl
    return result


def invalidate(cache_key: str) -> None:
    """手动清除指定缓存键"""
    _CACHE_STORE.pop(cache_key, None)
    _CACHE_TTL.pop(cache_key, None)


def invalidate_all() -> None:
    """清除全部缓存"""
    _CACHE_STORE.clear()
    _CACHE_TTL.clear()


def get_cache_info() -> dict[str, int]:
    """返回缓存统计信息"""
    now = time.time()
    alive = sum(1 for v in _CACHE_TTL.values() if v > now)
    return {
        "total_keys": len(_CACHE_STORE),
        "alive_keys": alive,
        "expired_keys": len(_CACHE_STORE) - alive,
    }
