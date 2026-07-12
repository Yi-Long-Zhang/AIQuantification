import json
from typing import Any

from models.schemas import AgentMessage
from .config import settings
from .llm_client import LLMClient
from .memory import AgentMemory
from .tools.registry import get_tool_definitions, execute_tool


SYSTEM_PROMPT = """You are an expert quantitative trading analyst AI assistant.

Your capabilities:
- Fetch real-time and historical market data (US/CN/HK stocks, crypto)
- Calculate technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands, ATR, etc.)
- Run backtests on different trading strategies
- Calculate position sizes and assess portfolio risk
- Get market news and sentiment analysis
- Calculate quant factors (momentum, volatility, etc.)

Decision-making process:
1. First gather data using tools to cover at least 3 analysis dimensions
2. Then synthesize and weigh evidence from each dimension
3. Assign a signal level (STRONG_BUY / BUY / HOLD / SELL / STRONG_SELL)
4. Assign a confidence score (0.0 ~ 1.0)
5. Calculate position size using risk rules
6. Always include stop-loss and take-profit levels

When responding:
- Show your reasoning process clearly, referencing the constitution where applicable
- Use markdown for structured responses
- Include specific numbers and percentages
- If data is insufficient, say so and suggest what would help
- End each analysis with a clear summary table of signals

You trade UTC timezone. Any violation of the constitution must be recorded."""


class QuantAgent:
    def __init__(
        self,
        llm_provider: str | None = None,
        llm_model: str | None = None,
        db_path: str | None = None,
    ):
        self.llm = LLMClient(provider=llm_provider, model=llm_model)
        self.memory = AgentMemory(db_path=db_path or settings.memory_db_path)
        self.tools = get_tool_definitions()

    def _convert_history(self, history: list[dict]) -> list[dict[str, Any]]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history[-20:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant", "system"):
                messages.append({"role": role, "content": content})
        return messages

    async def chat(self, query: str, session_id: str) -> str:
        self.memory.create_session(session_id)
        history = self.memory.get_history(session_id)
        messages = self._convert_history(history)
        messages.append({"role": "user", "content": query})
        self.memory.save_message(session_id, "user", query)

        response = await self._run_loop(messages, session_id)
        self.memory.save_message(session_id, "assistant", response)
        return response

    async def _run_loop(self, messages: list[dict], session_id: str, max_iterations: int = 10) -> str:
        for iteration in range(max_iterations):
            result = await self.llm.chat(messages, tools=self.tools)

            choice = result.get("choices", [{}])[0]
            message = choice.get("message", {})
            content = message.get("content") or ""
            tool_calls = message.get("tool_calls")

            if not tool_calls:
                return content

            messages.append({"role": "assistant", "content": content, "tool_calls": tool_calls})

            for tc in tool_calls:
                func_name = tc["function"]["name"]
                try:
                    args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    args = {}

                try:
                    tool_result = await execute_tool(func_name, **args)
                    result_str = json.dumps(tool_result, ensure_ascii=False, default=str)
                except Exception as e:
                    result_str = json.dumps({"error": str(e)})

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result_str[:50000],
                })

                meta = {"tool": func_name, "args": args}
                self.memory.save_message(session_id, "assistant",
                                          f"[Tool: {func_name}] {result_str[:500]}", metadata=meta)

        return "I've completed my analysis. The maximum number of tool interactions has been reached. Here's what I found based on the data collected so far."

    async def stream_chat(self, query: str, session_id: str):
        self.memory.create_session(session_id)
        history = self.memory.get_history(session_id)
        messages = self._convert_history(history)
        messages.append({"role": "user", "content": query})
        self.memory.save_message(session_id, "user", query)

        accumulated = ""
        async for chunk in self.llm.chat_stream(messages, tools=self.tools):
            delta = chunk.get("choices", [{}])[0].get("delta", {})
            content = delta.get("content", "")
            if content:
                accumulated += content
                yield content

        if accumulated:
            self.memory.save_message(session_id, "assistant", accumulated)

    async def close(self):
        await self.llm.close()
        self.memory.close()
