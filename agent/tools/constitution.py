from __future__ import annotations

import logging
from pathlib import Path

from .registry import tool

logger = logging.getLogger(__name__)


@tool(
    name="check_constitution",
    description="查询智能体宪法条款，确认行为是否合规",
    parameters={
        "article": {"type": "string", "description": "要查询的条款关键词，如 '风控原则', '仓位管理', '止损'", "default": ""},
    },
)
async def check_constitution(article: str = "") -> dict:
    # Try settings first, fall back to default path
    try:
        from agent.config import settings
        constitution_path = Path(settings.constitution_path) if settings.constitution_path else None
    except Exception as e:
        logger.debug("Failed to read constitution_path from settings: %s", e)
        constitution_path = None

    path = constitution_path or (Path(__file__).parent.parent.parent / "docs" / "agent-constitution.md")
    if not path.exists():
        return {"error": "Constitution not found"}

    text = path.read_text(encoding="utf-8")

    if article:
        sections = text.split("\n## ")
        matching = []
        for sec in sections:
            if article.lower() in sec.lower():
                matching.append(f"## {sec.strip()}")
        if matching:
            return {"query": article, "matches": matching, "count": len(matching)}
        return {"query": article, "matches": [], "message": "No matching articles found"}

    return {
        "constitution": text[:3000],
        "articles": ["总则", "风控原则", "数据原则", "决策框架", "伦理准则", "运营规则", "宪法修正"],
    }
