from abc import ABC, abstractmethod

import pandas as pd


class Strategy(ABC):
    name: str = "base"
    description: str = "Base strategy"
    type: str = "其他"
    tags: list[str] = []
    markets: list[str] = ["us_stock", "cn_stock", "hk_stock", "crypto"]
    params: dict[str, str] = {}
    risk_level: str = "中"  # 低/中/高

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        ...
