from abc import ABC, abstractmethod

import pandas as pd


class Strategy(ABC):
    name: str = "base"
    description: str = "Base strategy"

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        ...
