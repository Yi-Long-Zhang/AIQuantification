import pandas as pd

from .registry import tool


def _sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(window=length).mean()


def _ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def _rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=length).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
    rs = gain / loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def _macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    ema_fast = _ema(series, fast)
    ema_slow = _ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = _ema(macd_line, signal)
    histogram = macd_line - signal_line
    return pd.DataFrame({
        "MACD_12_26_9": macd_line,
        "MACDs_12_26_9": signal_line,
        "MACDh_12_26_9": histogram,
    })


def _bbands(series: pd.Series, length: int = 20, std: float = 2.0) -> pd.DataFrame:
    middle = _sma(series, length)
    rolling_std = series.rolling(window=length).std()
    upper = middle + std * rolling_std
    lower = middle - std * rolling_std
    return pd.DataFrame({
        "BBL_20_2.0": lower,
        "BBM_20_2.0": middle,
        "BBU_20_2.0": upper,
    })


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=length).mean()


def _stoch(high: pd.Series, low: pd.Series, close: pd.Series, k: int = 14, d: int = 3) -> pd.DataFrame:
    lowest_low = low.rolling(window=k).min()
    highest_high = high.rolling(window=k).max()
    stoch_k = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, pd.NA)
    stoch_d = stoch_k.rolling(window=d).mean()
    return pd.DataFrame({
        "STOCHk_14_3_3": stoch_k,
        "STOCHd_14_3_3": stoch_d,
    })


def _adx(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.DataFrame:
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

    atr_val = _atr(high, low, close, length)

    plus_di = 100 * _ema(plus_dm, length) / atr_val.replace(0, pd.NA)
    minus_di = 100 * _ema(minus_dm, length) / atr_val.replace(0, pd.NA)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, pd.NA)
    adx = _ema(dx, length)

    return pd.DataFrame({
        "ADX_14": adx,
        "DMP_14": plus_di,
        "DMN_14": minus_di,
    })


@tool(
    name="calculate_indicators",
    description="计算技术指标",
    parameters={
        "symbol": {"type": "string", "description": "股票代码"},
        "market": {"type": "string", "description": "市场", "default": "us_stock"},
        "indicators": {
            "type": "array",
            "items": {"type": "string"},
            "description": "指标列表: sma, ema, rsi, macd, bb, atr, stochastic, adx",
        },
    },
)
async def calculate_indicators(symbol: str, market: str = "us_stock", indicators: list[str] | None = None) -> dict:
    from .market_data import get_klines
    klines = await get_klines(symbol, market, interval="1d", period="6mo")
    if not klines:
        return {"error": "No data"}

    df = pd.DataFrame(klines)
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if indicators is None:
        indicators = ["sma", "ema", "rsi", "macd", "bb"]

    result = {"symbol": symbol, "latest": {}}
    ohlc = df[["Open", "High", "Low", "Close", "Volume"]].copy()

    for ind in indicators:
        try:
            if ind == "sma":
                sma20 = _sma(ohlc["Close"], 20)
                sma50 = _sma(ohlc["Close"], 50)
                result["latest"]["sma20"] = round(sma20.iloc[-1], 2) if not sma20.empty and pd.notna(sma20.iloc[-1]) else None
                result["latest"]["sma50"] = round(sma50.iloc[-1], 2) if not sma50.empty and pd.notna(sma50.iloc[-1]) else None
                result["sma_trend"] = "bullish" if result["latest"].get("sma20", 0) > result["latest"].get("sma50", 0) else "bearish"

            elif ind == "ema":
                ema12 = _ema(ohlc["Close"], 12)
                ema26 = _ema(ohlc["Close"], 26)
                result["latest"]["ema12"] = round(ema12.iloc[-1], 2) if not ema12.empty and pd.notna(ema12.iloc[-1]) else None
                result["latest"]["ema26"] = round(ema26.iloc[-1], 2) if not ema26.empty and pd.notna(ema26.iloc[-1]) else None

            elif ind == "rsi":
                rsi = _rsi(ohlc["Close"], 14)
                val = rsi.iloc[-1] if not rsi.empty and pd.notna(rsi.iloc[-1]) else None
                result["latest"]["rsi14"] = round(val, 2) if val else None
                if val is not None:
                    result["rsi_signal"] = "overbought" if val > 70 else "oversold" if val < 30 else "neutral"

            elif ind == "macd":
                macd = _macd(ohlc["Close"])
                if macd is not None and not macd.empty:
                    result["latest"]["macd"] = round(macd.iloc[-1, 0], 4) if pd.notna(macd.iloc[-1, 0]) else None
                    result["latest"]["macd_signal"] = round(macd.iloc[-1, 1], 4) if macd.shape[1] > 1 and pd.notna(macd.iloc[-1, 1]) else None
                    result["latest"]["macd_histogram"] = round(macd.iloc[-1, 2], 4) if macd.shape[1] > 2 and pd.notna(macd.iloc[-1, 2]) else None
                    hist = result["latest"].get("macd_histogram")
                    if hist is not None:
                        pre = macd.iloc[-2, 2] if len(macd) > 1 and pd.notna(macd.iloc[-2, 2]) else 0
                        if hist > 0 and hist > pre:
                            result["macd_signal"] = "bullish_strengthening"
                        elif hist > 0 and hist < pre:
                            result["macd_signal"] = "bullish_weakening"
                        elif hist < 0 and hist < pre:
                            result["macd_signal"] = "bearish_strengthening"
                        elif hist < 0 and hist > pre:
                            result["macd_signal"] = "bearish_weakening"

            elif ind == "bb":
                bb = _bbands(ohlc["Close"], 20)
                if bb is not None and not bb.empty:
                    result["latest"]["bb_upper"] = round(bb.iloc[-1, 2], 2) if pd.notna(bb.iloc[-1, 2]) else None
                    result["latest"]["bb_middle"] = round(bb.iloc[-1, 1], 2) if bb.shape[1] > 1 and pd.notna(bb.iloc[-1, 1]) else None
                    result["latest"]["bb_lower"] = round(bb.iloc[-1, 0], 2) if bb.shape[1] > 2 and pd.notna(bb.iloc[-1, 0]) else None

            elif ind == "atr":
                atr = _atr(ohlc["High"], ohlc["Low"], ohlc["Close"], 14)
                val = atr.iloc[-1] if not atr.empty and pd.notna(atr.iloc[-1]) else None
                result["latest"]["atr14"] = round(val, 2) if val else None

            elif ind == "stochastic":
                stoch = _stoch(ohlc["High"], ohlc["Low"], ohlc["Close"])
                if stoch is not None and not stoch.empty:
                    result["latest"]["stoch_k"] = round(stoch.iloc[-1, 0], 2)
                    result["latest"]["stoch_d"] = round(stoch.iloc[-1, 1], 2)

            elif ind == "adx":
                adx = _adx(ohlc["High"], ohlc["Low"], ohlc["Close"])
                if adx is not None and not adx.empty:
                    result["latest"]["adx"] = round(adx.iloc[-1, 0], 2)
                    result["latest"]["dmp"] = round(adx.iloc[-1, 1], 2) if adx.shape[1] > 1 else None
                    result["latest"]["dmn"] = round(adx.iloc[-1, 2], 2) if adx.shape[1] > 2 else None

        except Exception:
            continue

    close = pd.to_numeric(df["Close"], errors="coerce")
    if len(close) > 1:
        result["latest"]["close"] = round(close.iloc[-1], 2)
        result["change_pct_1d"] = round((close.iloc[-1] / close.iloc[-2] - 1) * 100, 2) if pd.notna(close.iloc[-2]) and close.iloc[-2] != 0 else None

    return result


@tool(
    name="calculate_factor",
    description="计算量化因子值",
    parameters={
        "symbol": {"type": "string", "description": "股票代码"},
        "market": {"type": "string", "description": "市场", "default": "us_stock"},
        "factor_name": {"type": "string", "description": "因子名称: momentum, volatility, volume_ratio, price_to_sma"},
    },
)
async def calculate_factor(symbol: str, market: str = "us_stock", factor_name: str = "momentum") -> dict:
    from .market_data import get_klines
    klines = await get_klines(symbol, market, interval="1d", period="1y")
    if not klines:
        return {"error": "No data"}

    df = pd.DataFrame(klines)
    close = pd.to_numeric(df["Close"], errors="coerce")
    volume = pd.to_numeric(df["Volume"], errors="coerce")

    result = {"symbol": symbol, "factor": factor_name}

    if factor_name == "momentum":
        for period in [5, 10, 20, 60]:
            if len(close) > period:
                ret = (close.iloc[-1] / close.iloc[-period - 1] - 1) * 100
                result[f"momentum_{period}d"] = round(ret, 2)

    elif factor_name == "volatility":
        returns = close.pct_change().dropna()
        for period in [20, 60]:
            if len(returns) >= period:
                vol = returns.tail(period).std() * (252 ** 0.5)
                result[f"volatility_{period}d"] = round(vol * 100, 2)

    elif factor_name == "volume_ratio":
        if len(volume) > 20:
            avg_vol = volume.tail(20).mean()
            if avg_vol > 0:
                result["volume_ratio"] = round(volume.iloc[-1] / avg_vol, 2)

    elif factor_name == "price_to_sma":
        sma20 = close.rolling(20).mean()
        if len(close) > 20 and pd.notna(sma20.iloc[-1]) and sma20.iloc[-1] != 0:
            result["price_to_sma20"] = round(close.iloc[-1] / sma20.iloc[-1], 4)
        sma50 = close.rolling(50).mean()
        if len(close) > 50 and pd.notna(sma50.iloc[-1]) and sma50.iloc[-1] != 0:
            result["price_to_sma50"] = round(close.iloc[-1] / sma50.iloc[-1], 4)

    return result
