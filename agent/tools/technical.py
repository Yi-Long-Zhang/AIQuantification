import pandas as pd
import pandas_ta as ta

from .registry import tool


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
                sma20 = ta.sma(ohlc["Close"], length=20)
                sma50 = ta.sma(ohlc["Close"], length=50)
                result["latest"]["sma20"] = round(sma20.iloc[-1], 2) if not sma20.empty and pd.notna(sma20.iloc[-1]) else None
                result["latest"]["sma50"] = round(sma50.iloc[-1], 2) if not sma50.empty and pd.notna(sma50.iloc[-1]) else None
                result["sma_trend"] = "bullish" if result["latest"].get("sma20", 0) > result["latest"].get("sma50", 0) else "bearish"

            elif ind == "ema":
                ema12 = ta.ema(ohlc["Close"], length=12)
                ema26 = ta.ema(ohlc["Close"], length=26)
                result["latest"]["ema12"] = round(ema12.iloc[-1], 2) if not ema12.empty and pd.notna(ema12.iloc[-1]) else None
                result["latest"]["ema26"] = round(ema26.iloc[-1], 2) if not ema26.empty and pd.notna(ema26.iloc[-1]) else None

            elif ind == "rsi":
                rsi = ta.rsi(ohlc["Close"], length=14)
                val = rsi.iloc[-1] if not rsi.empty and pd.notna(rsi.iloc[-1]) else None
                result["latest"]["rsi14"] = round(val, 2) if val else None
                if val is not None:
                    result["rsi_signal"] = "overbought" if val > 70 else "oversold" if val < 30 else "neutral"

            elif ind == "macd":
                macd = ta.macd(ohlc["Close"])
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
                bb = ta.bbands(ohlc["Close"], length=20)
                if bb is not None and not bb.empty:
                    result["latest"]["bb_upper"] = round(bb.iloc[-1, 0], 2) if pd.notna(bb.iloc[-1, 0]) else None
                    result["latest"]["bb_middle"] = round(bb.iloc[-1, 1], 2) if bb.shape[1] > 1 and pd.notna(bb.iloc[-1, 1]) else None
                    result["latest"]["bb_lower"] = round(bb.iloc[-1, 2], 2) if bb.shape[1] > 2 and pd.notna(bb.iloc[-1, 2]) else None

            elif ind == "atr":
                atr = ta.atr(ohlc["High"], ohlc["Low"], ohlc["Close"], length=14)
                val = atr.iloc[-1] if not atr.empty and pd.notna(atr.iloc[-1]) else None
                result["latest"]["atr14"] = round(val, 2) if val else None

            elif ind == "stochastic":
                stoch = ta.stoch(ohlc["High"], ohlc["Low"], ohlc["Close"])
                if stoch is not None and not stoch.empty:
                    result["latest"]["stoch_k"] = round(stoch.iloc[-1, 0], 2)
                    result["latest"]["stoch_d"] = round(stoch.iloc[-1, 1], 2)

            elif ind == "adx":
                adx = ta.adx(ohlc["High"], ohlc["Low"], ohlc["Close"])
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
