from abc import ABC, abstractmethod

import pandas as pd


class Strategy(ABC):
    name: str = "base"
    description: str = "Base strategy"
    type: str = "其他"  # 趋势/反转/均值回归/事件驱动/组合
    tags: list[str] = []  # 如 ["momentum", "mean-reversion", "breakout"]

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        ...
