from __future__ import annotations

import pytest


def test_skill_registry():
    from agent.skills import SkillRegistry, Skill
    registry = SkillRegistry()
    skill = Skill(name="test", description="Test skill", tools=["tool1"])
    registry.register(skill)
    assert registry.get("test") is not None
    assert "test" in registry.list_names()


def test_load_all_skills():
    from agent.skills import load_all_skills, get_skill_registry
    skills = load_all_skills()
    assert len(skills) >= 3
    registry = get_skill_registry()
    assert "hk_fund_flow" in registry.list_names()
    assert "crypto_sentiment" in registry.list_names()
    assert "multi_market_compare" in registry.list_names()


def test_skill_search_by_tag():
    from agent.skills import load_all_skills, get_skill_registry
    load_all_skills()
    registry = get_skill_registry()
    crypto_skills = registry.search_by_tag("crypto")
    assert len(crypto_skills) >= 1


def test_skill_search_by_tool():
    from agent.skills import load_all_skills, get_skill_registry
    load_all_skills()
    registry = get_skill_registry()
    skills = registry.search_by_tool("get_hk_flow")
    assert len(skills) >= 1


def test_skill_to_dict():
    from agent.skills import Skill
    skill = Skill(name="test", description="Test", tools=["t1"], tags=["tag1"])
    d = skill.to_dict()
    assert d["name"] == "test"
    assert d["tools"] == ["t1"]
    assert d["tags"] == ["tag1"]
