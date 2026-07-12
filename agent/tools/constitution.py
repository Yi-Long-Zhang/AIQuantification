from pathlib import Path

from .registry import tool


@tool(
    name="check_constitution",
    description="查询智能体宪法条款，确认行为是否合规",
    parameters={
        "article": {"type": "string", "description": "要查询的条款关键词，如 '风控原则', '仓位管理', '止损'", "default": ""},
    },
)
async def check_constitution(article: str = "") -> dict:
    path = Path(__file__).parent.parent.parent / "AGENT_CONSTITUTION.md"
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
