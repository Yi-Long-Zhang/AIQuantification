"""
Strategy Registry — central lookup for all strategies.

Strategy classes are defined in category files (trend_strategies.py,
mean_reversion_strategies.py, specialized_strategies.py) and imported here
into a single _STRATEGIES dictionary.
"""

from __future__ import annotations

from typing import Any

from .base import Strategy

from .trend_strategies import (
    SMACrossStrategy, MACDStrategy, IchimokuStrategy, SMCStrategy,
    ATRChannelStrategy, ParabolicSARStrategy, VolumeWeightedMomentumStrategy,
    DonchianChannelStrategy, KeltnerChannelStrategy,
)
from .mean_reversion_strategies import (
    BollingerStrategy, ZScoreMeanReversionStrategy,
    PairTradingStrategy, GapFillStrategy,
)
from .specialized_strategies import (
    RSIStrategy, RSIDivergenceStrategy, MultiFactorStrategy,
    CryptoFundingStrategy, EarningsMomentumStrategy,
)


_STRATEGIES: dict[str, type[Strategy]] = {
    "sma_cross": SMACrossStrategy, "macd": MACDStrategy,
    "rsi": RSIStrategy, "bollinger": BollingerStrategy,
    "ichimoku": IchimokuStrategy, "smc": SMCStrategy,
    "multi_factor": MultiFactorStrategy, "crypto_funding": CryptoFundingStrategy,
    "atr_channel": ATRChannelStrategy, "parabolic_sar": ParabolicSARStrategy,
    "zscore_mean_reversion": ZScoreMeanReversionStrategy,
    "pair_trading": PairTradingStrategy,
    "volume_weighted_momentum": VolumeWeightedMomentumStrategy,
    "gap_fill": GapFillStrategy, "rsi_divergence": RSIDivergenceStrategy,
    "earnings_momentum": EarningsMomentumStrategy,
    "donchian_channel": DonchianChannelStrategy,
    "keltner_channel": KeltnerChannelStrategy,
}


def get_strategy(name: str) -> Strategy | None:
    cls = _STRATEGIES.get(name)
    if cls:
        return cls()
    return None


def list_strategies() -> list[dict[str, Any]]:
    return [{"name": s.name, "description": s.description, "type": s.type,
             "tags": s.tags, "markets": s.markets, "params": s.params,
             "risk_level": s.risk_level} for s in _STRATEGIES.values()]
