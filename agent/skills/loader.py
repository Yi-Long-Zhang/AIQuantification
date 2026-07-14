from __future__ import annotations

import logging
from pathlib import Path

import yaml

from .registry import Skill, SkillRegistry, get_skill_registry

logger = logging.getLogger(__name__)

_SKILLS_DIR = Path(__file__).parent / "skills"


def _load_skill_from_yaml(yaml_path: Path) -> Skill | None:
    try:
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            return None
        return Skill(
            name=data.get("name", yaml_path.stem),
            description=data.get("description", ""),
            tools=data.get("tools", []),
            prompt_template=data.get("prompt_template", ""),
            tags=data.get("tags", []),
        )
    except Exception as e:
        logger.warning("Failed to load skill from %s: %s", yaml_path, e)
        return None


def load_all_skills(skills_dir: Path | None = None) -> list[Skill]:
    directory = skills_dir or _SKILLS_DIR
    registry = get_skill_registry()
    loaded = []
    if not directory.exists():
        return loaded
    for yaml_file in sorted(directory.glob("*.yaml")):
        skill = _load_skill_from_yaml(yaml_file)
        if skill:
            registry.register(skill)
            loaded.append(skill)
    for yml_file in sorted(directory.glob("*.yml")):
        skill = _load_skill_from_yaml(yml_file)
        if skill:
            registry.register(skill)
            loaded.append(skill)
    logger.info("Loaded %d skills from %s", len(loaded), directory)
    return loaded
