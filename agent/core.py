from __future__ import annotations

import json
from typing import Any

from .config import settings
from .llm_client import LLMClient
from .memory import AsyncAgentMemory
from .tools.registry import get_tool_definitions, execute_tool
from .skills import load_all_skills, get_skill_registry


SYSTEM_PROMPT = """You are an expert quantitative trading analyst AI assistant.

Your capabilities:
- Fetch real-time and historical market data (US/CN/HK stocks, crypto)
- Calculate technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands, ATR, etc.)
- Run backtests on different trading strategies
- Calculate position sizes and assess portfolio risk
- Get market news and sentiment analysis
- Calculate quant factors (momentum, volatility, etc.)
- Use specialized analysis skills for comprehensive insights
- Compute and evaluate Alpha101/Alpha158 factor models with IC, IR, turnover, and Sharpe metrics

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
        self.memory = AsyncAgentMemory(db_path=db_path or settings.memory_db_path)
        load_all_skills()
        self.tools = get_tool_definitions() + self._get_skill_definitions()

    def _get_skill_definitions(self) -> list[dict[str, Any]]:
        registry = get_skill_registry()
        return [
            {
                "type": "function",
                "function": {
                    "name": f"skill_{skill_dict['name']}",
                    "description": f"[Skill] {skill_dict['description']}",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Analysis request for this skill"},
                        },
                        "required": ["query"],
                    },
                },
            }
            for skill_dict in registry.list_all()
        ]

    def _convert_history(self, history: list[dict]) -> list[dict[str, Any]]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history[-20:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant", "system"):
                messages.append({"role": role, "content": content})
        return messages

    async def _execute_skill(self, skill_name: str, args: dict, session_id: str) -> str:
        registry = get_skill_registry()
        skill = registry.get(skill_name)
        if not skill:
            return json.dumps({"error": f"Skill '{skill_name}' not found"})

        query = args.get("query", "")
        skill_prompt = skill.prompt_template + "\n\nUser request: " + query

        tool_results = {}
        for tool_name in skill.tools:
            try:
                params = skill.tool_params.get(tool_name, {})
                result = await execute_tool(tool_name, **params)
                tool_results[tool_name] = result
            except Exception as e:
                tool_results[tool_name] = {"error": str(e)}

        messages = [
            {"role": "system", "content": skill_prompt},
            {"role": "user", "content": f"Analyze based on this data:\n{json.dumps(tool_results, ensure_ascii=False, default=str)[:50000]}"},
        ]
        result = await self.llm.chat(messages)
        return result.get("choices", [{}])[0].get("message", {}).get("content", "")

    async def chat(self, query: str, session_id: str) -> str:
        await self.memory.create_session(session_id)
        history = await self.memory.get_history(session_id)
        messages = self._convert_history(history)
        messages.append({"role": "user", "content": query})
        await self.memory.save_message(session_id, "user", query)

        response = await self._run_loop(messages, session_id)
        await self.memory.save_message(session_id, "assistant", response)
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
                    if func_name.startswith("skill_"):
                        skill_name = func_name[6:]
                        result_str = await self._execute_skill(skill_name, args, session_id)
                    else:
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
                await self.memory.save_message(session_id, "assistant",
                                           f"[Tool: {func_name}] {result_str[:500]}", metadata=meta)

        return "I've completed my analysis. The maximum number of tool interactions has been reached. Here's what I found based on the data collected so far."

    async def stream_chat(self, query: str, session_id: str):
        await self.memory.create_session(session_id)
        history = await self.memory.get_history(session_id)
        messages = self._convert_history(history)
        messages.append({"role": "user", "content": query})
        await self.memory.save_message(session_id, "user", query)

        accumulated = ""
        tool_calls_buffer: list[dict] = []
        current_tool_call: dict | None = None

        async for chunk in self.llm.chat_stream(messages, tools=self.tools):
            delta = chunk.get("choices", [{}])[0].get("delta", {})

            content = delta.get("content", "")
            if content:
                accumulated += content
                yield content

            delta_tool_calls = delta.get("tool_calls")
            if delta_tool_calls:
                for tc_delta in delta_tool_calls:
                    tc_index = tc_delta.get("index", 0)

                    if tc_index >= len(tool_calls_buffer):
                        tool_calls_buffer.append({
                            "id": tc_delta.get("id", ""),
                            "function": {"name": "", "arguments": ""},
                        })

                    tc = tool_calls_buffer[tc_index]
                    if tc_delta.get("id"):
                        tc["id"] = tc_delta["id"]
                    func_delta = tc_delta.get("function", {})
                    if func_delta.get("name"):
                        tc["function"]["name"] += func_delta["name"]
                    if func_delta.get("arguments"):
                        tc["function"]["arguments"] += func_delta["arguments"]

        if tool_calls_buffer:
            messages.append({"role": "assistant", "content": accumulated or None, "tool_calls": tool_calls_buffer})

            for tc in tool_calls_buffer:
                func_name = tc["function"]["name"]
                try:
                    args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    args = {}

                yield f"\n\n🔧 调用工具: {func_name}\n"

                try:
                    if func_name.startswith("skill_"):
                        skill_name = func_name[6:]
                        result_str = await self._execute_skill(skill_name, args, session_id)
                    else:
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
                await self.memory.save_message(session_id, "assistant",
                                           f"[Tool: {func_name}] {result_str[:500]}", metadata=meta)

            final_accumulated = ""
            async for chunk in self.llm.chat_stream(messages, tools=self.tools):
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    final_accumulated += content
                    yield content

            accumulated = (accumulated + "\n\n" + final_accumulated).strip() if final_accumulated else accumulated

        if accumulated:
            await self.memory.save_message(session_id, "assistant", accumulated)

    async def close(self):
        await self.llm.close()
        await self.memory.close()
