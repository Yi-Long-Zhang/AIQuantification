"""
Tests for Markdown skill loader
"""

import pytest
from pathlib import Path
from agent.skills.loader import _parse_markdown_skill, load_all_skills


def test_parse_markdown_skill(tmp_path):
    """Test parsing a Markdown skill file."""
    skill_content = """---
name: test_skill
description: A test skill
tools:
  - get_stock_quote
  - calculate_sma
tags:
  - test
---

# Test Skill

This is a test skill with markdown content.

## Instructions
- Do something
- Do something else
"""

    skill_file = tmp_path / "test_skill.md"
    skill_file.write_text(skill_content, encoding="utf-8")

    skill = _parse_markdown_skill(skill_file)

    assert skill is not None
    assert skill.name == "test_skill"
    assert skill.description == "A test skill"
    assert skill.tools == ["get_stock_quote", "calculate_sma"]
    assert skill.tags == ["test"]
    assert "Test Skill" in skill.prompt_template
    assert "Instructions" in skill.prompt_template


def test_parse_markdown_skill_no_frontmatter(tmp_path):
    """Test parsing a Markdown file without frontmatter."""
    skill_file = tmp_path / "invalid.md"
    skill_file.write_text("# Just content\nNo frontmatter", encoding="utf-8")

    skill = _parse_markdown_skill(skill_file)
    assert skill is None


def test_load_all_skills_empty_dir(tmp_path):
    """Test loading skills from an empty directory."""
    skills = load_all_skills(tmp_path)
    assert skills == []


def test_load_all_skills_mixed_formats(tmp_path):
    """Test loading both MD and YAML skills."""
    # Create MD skill
    md_content = """---
name: md_skill
description: MD skill
tools: []
---

# MD Skill Content
"""
    (tmp_path / "md_skill.md").write_text(md_content, encoding="utf-8")

    # Create YAML skill
    yaml_content = """name: yaml_skill
description: YAML skill
tools: []
prompt_template: YAML prompt
"""
    (tmp_path / "yaml_skill.yaml").write_text(yaml_content, encoding="utf-8")

    skills = load_all_skills(tmp_path)

    assert len(skills) == 2
    skill_names = {s.name for s in skills}
    assert "md_skill" in skill_names
    assert "yaml_skill" in skill_names
