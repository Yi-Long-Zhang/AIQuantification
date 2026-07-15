from __future__ import annotations

import logging
import re
from pathlib import Path

import yaml

from .registry import Skill, SkillRegistry, get_skill_registry

logger = logging.getLogger(__name__)

_SKILLS_DIR = Path(__file__).parent / "skills"


def _parse_markdown_skill(md_path: Path) -> Skill | None:
    """
    Parse a Markdown skill file with YAML frontmatter.

    Format:
    ---
    name: skill_name
    description: ...
    tools: [...]
    tags: [...]
    ---

    # Skill content in Markdown
    """
    try:
        with open(md_path, encoding="utf-8") as f:
            content = f.read()

        # Extract YAML frontmatter
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
        if not match:
            logger.warning("No frontmatter found in %s", md_path)
            return None

        frontmatter_str, body = match.groups()

        # Parse YAML frontmatter
        metadata = yaml.safe_load(frontmatter_str)
        if not metadata:
            return None

        return Skill(
            name=metadata.get("name", md_path.stem),
            description=metadata.get("description", ""),
            tools=metadata.get("tools", []),
            tool_params=metadata.get("tool_params", {}),
            prompt_template=body.strip(),
            tags=metadata.get("tags", []),
        )
    except Exception as e:
        logger.warning("Failed to load skill from %s: %s", md_path, e)
        return None


def _load_skill_from_yaml(yaml_path: Path) -> Skill | None:
    """Load skill from legacy YAML format (for backward compatibility)."""
    try:
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            return None
        return Skill(
            name=data.get("name", yaml_path.stem),
            description=data.get("description", ""),
            tools=data.get("tools", []),
            tool_params=data.get("tool_params", {}),
            prompt_template=data.get("prompt_template", ""),
            tags=data.get("tags", []),
        )
    except Exception as e:
        logger.warning("Failed to load skill from %s: %s", yaml_path, e)
        return None


def load_all_skills(skills_dir: Path | None = None) -> list[Skill]:
    """
    Load all skills from a directory.

    Supports both:
    - Markdown files with YAML frontmatter (.md) - PREFERRED
    - Legacy YAML files (.yaml, .yml)
    """
    directory = skills_dir or _SKILLS_DIR
    registry = get_skill_registry()
    loaded = []

    if not directory.exists():
        return loaded

    # Load Markdown skills (preferred format)
    for md_file in sorted(directory.glob("*.md")):
        skill = _parse_markdown_skill(md_file)
        if skill:
            registry.register(skill)
            loaded.append(skill)
            logger.info("Loaded MD skill: %s", skill.name)

    # Load legacy YAML skills (backward compatibility)
    for yaml_file in sorted(directory.glob("*.yaml")):
        skill = _load_skill_from_yaml(yaml_file)
        if skill:
            registry.register(skill)
            loaded.append(skill)
            logger.info("Loaded YAML skill: %s", skill.name)

    for yml_file in sorted(directory.glob("*.yml")):
        skill = _load_skill_from_yaml(yml_file)
        if skill:
            registry.register(skill)
            loaded.append(skill)
            logger.info("Loaded YAML skill: %s", skill.name)

    logger.info("Loaded %d skills from %s", len(loaded), directory)
    return loaded
