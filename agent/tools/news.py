from __future__ import annotations

import asyncio

from .registry import tool


@tool(
    name="get_stock_news",
    description="获取股票相关新闻",
    parameters={
        "symbol": {"type": "string", "description": "股票代码"},
        "market": {"type": "string", "description": "市场", "default": "us_stock"},
        "max_news": {"type": "integer", "description": "最大新闻条数", "default": 5},
    },
)
async def get_stock_news(symbol: str, market: str = "us_stock", max_news: int = 5) -> list[dict]:
    import yfinance as yf

    def _fetch():
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            if not news:
                return []
            results = []
            for article in news[:max_news]:
                results.append({
                    "title": article.get("title", ""),
                    "publisher": article.get("publisher", ""),
                    "link": article.get("link", ""),
                    "type": article.get("type", ""),
                })
            return results
        except Exception as e:
            return [{"error": str(e)}]

    return await asyncio.to_thread(_fetch)


@tool(
    name="analyze_sentiment",
    description="分析市场情绪（恐慌贪婪指数）",
    parameters={
        "market": {"type": "string", "description": "市场: crypto, us_stock", "default": "crypto"},
    },
)
async def analyze_sentiment(market: str = "crypto") -> dict:
    import httpx
    result = {"market": market}

    if market == "crypto":
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get("https://api.alternative.me/fng/?limit=1")
                data = resp.json()
                if data.get("data"):
                    item = data["data"][0]
                    result["fear_greed_index"] = int(item.get("value", 50))
                    result["classification"] = item.get("value_classification", "Neutral")
        except Exception:
            result["fear_greed_index"] = None
            result["classification"] = "Unknown"

    elif market == "us_stock":
        import yfinance as yf

        def _fetch():
            try:
                cboe = yf.Ticker("^VIX")
                info = cboe.info
                vix = info.get("regularMarketPrice")
                result["vix"] = vix
                if vix is not None:
                    if vix < 15:
                        result["classification"] = "Low Fear"
                    elif vix < 25:
                        result["classification"] = "Moderate"
                    elif vix < 35:
                        result["classification"] = "High Fear"
                    else:
                        result["classification"] = "Extreme Fear"
            except Exception:
                result["vix"] = None
                result["classification"] = "Unknown"

        await asyncio.to_thread(_fetch)

    return result
