from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Skill:
    """技能定义"""
    name: str
    description: str
    tools: list[str] = field(default_factory=list)
    tool_params: dict[str, dict[str, Any]] = field(default_factory=dict)
    prompt_template: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "tools": self.tools,
            "tool_params": self.tool_params,
            "prompt_template": self.prompt_template,
            "tags": self.tags,
        }


class SkillRegistry:
    """技能注册中心"""

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def list_all(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self._skills.values()]

    def list_names(self) -> list[str]:
        return list(self._skills.keys())

    def search_by_tag(self, tag: str) -> list[Skill]:
        return [s for s in self._skills.values() if tag in s.tags]

    def search_by_tool(self, tool_name: str) -> list[Skill]:
        return [s for s in self._skills.values() if tool_name in s.tools]


_registry = SkillRegistry()


def get_skill_registry() -> SkillRegistry:
    return _registry
