"""
Decision Synthesis — LLM synthesis, signal extraction, risk filtering

Extracted from CoordinatorAgent to keep each file under 500 lines.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class DecisionSynthesizerMixin:
    """Mixin providing decision synthesis methods for CoordinatorAgent."""

    async def _synthesize_decision(
        self,
        research: dict,
        strategy: dict,
        risk: dict
    ) -> dict:
        """Ask LLM to synthesize a final trading decision."""
        approved_signals = risk.get("approved_signals", [])
        if not approved_signals:
            return {
                "action": "HOLD",
                "signals": [],
                "confidence": 0.0,
                "reasoning": "No approved signals after risk assessment",
                "risk_approved": False
            }

        prompt = f"""You are the final decision maker in a quantitative trading system.

Based on multi-agent analysis, synthesize the final decision.

Research Summary: {research.get('summary', {})}
Strategy Signals: {strategy.get('signals', [])}
Risk-Approved Signals: {approved_signals}

Confidence calibration:
- 0.85-1.0: multiple agents agree, strong signals, low macro risk
- 0.65-0.84: 2+ agents agree, moderate signals
- 0.50-0.64: mixed signals, cautious entry
- <0.50: hold, insufficient evidence

Provide ONLY the top 3 signals with specific entry/stop/take-profit levels.
Every decision MUST include reasoning that references WHICH agent provided the signal."""

        schema = {
            "type": "object",
            "properties": {
                "decisions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string"},
                            "action": {"type": "string"},
                            "confidence": {"type": "number"},
                            "entry_price": {"type": "number"},
                            "stop_loss": {"type": "number"},
                            "take_profit": {"type": "number"},
                            "reasoning": {"type": "string"}
                        }
                    }
                },
                "market_view": {"type": "string"},
                "overall_confidence": {"type": "number"}
            }
        }

        try:
            result = await self.ask_llm_structured(prompt, schema)
            result["risk_approved"] = True
            return result
        except Exception as e:
            logger.error(f"Decision synthesis failed: {e}")
            return {
                "decisions": approved_signals,
                "market_view": "Unknown",
                "overall_confidence": 0.5,
                "risk_approved": True,
                "error": str(e)
            }

    def _summarize_research(self, results: dict) -> dict:
        """Summarize research results across agents."""
        successful = {k: v for k, v in results.items() if v.get("status") == "SUCCESS"}
        return {
            "total_agents": len(results),
            "successful": len(successful),
            "data_points": sum(
                len(v.get("output", {})) for v in successful.values()
            )
        }

    def _extract_signals(self, results: dict) -> list[dict]:
        """Extract trading signals from strategy agent results."""
        signals = []
        for agent_name, result in results.items():
            if result.get("status") == "SUCCESS":
                output = result.get("output", {})
                if "signal" in output:
                    signals.append(output["signal"])
                elif "signals" in output:
                    signals.extend(output["signals"])
        return signals

    def _filter_signals(
        self,
        signals: list[dict],
        risk_results: dict
    ) -> tuple[list[dict], list[dict]]:
        """Split signals into approved and rejected based on risk assessment."""
        vetoes = set()
        for result in risk_results.values():
            if result.get("status") == "SUCCESS":
                rejected = result.get("output", {}).get("rejected_symbols", [])
                vetoes.update(rejected)

        approved = [s for s in signals if s.get("symbol") not in vetoes]
        rejected = [s for s in signals if s.get("symbol") in vetoes]
        return approved, rejected
