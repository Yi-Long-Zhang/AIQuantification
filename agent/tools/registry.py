from __future__ import annotations

import inspect
from typing import Any, Callable

_TOOL_REGISTRY: dict[str, dict[str, Any]] = {}


def tool(name: str, description: str, parameters: dict[str, Any] | None = None):
    def decorator(func: Callable) -> Callable:
        sig = inspect.signature(func)
        props = {}
        required = []
        for p_name, p_param in sig.parameters.items():
            p_type = "string"
            if p_param.annotation is not inspect.Parameter.empty:
                type_map = {str: "string", int: "integer", float: "number", bool: "boolean", list: "array", dict: "object"}
                p_type = type_map.get(p_param.annotation, "string")
            p_desc = ""
            if parameters and p_name in parameters:
                p_desc = parameters[p_name].get("description", "")
                if "type" in parameters[p_name]:
                    p_type = parameters[p_name]["type"]
                if "items" in parameters[p_name]:
                    props[p_name] = {"type": p_type, "description": p_desc, "items": parameters[p_name]["items"]}
                    continue
            props[p_name] = {"type": p_type, "description": p_desc}
            if p_param.default is inspect.Parameter.empty:
                required.append(p_name)

        tool_def = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": props,
                    "required": required,
                },
            },
        }
        _TOOL_REGISTRY[name] = {"func": func, "definition": tool_def}
        return func

    return decorator


def get_tool_definitions() -> list[dict[str, Any]]:
    return [v["definition"] for v in _TOOL_REGISTRY.values()]


def get_tool_names() -> list[str]:
    return list(_TOOL_REGISTRY.keys())


async def execute_tool(name: str, **kwargs) -> Any:
    entry = _TOOL_REGISTRY.get(name)
    if not entry:
        raise ValueError(f"Unknown tool: {name}")
    func = entry["func"]
    if inspect.iscoroutinefunction(func):
        return await func(**kwargs)
    return func(**kwargs)
