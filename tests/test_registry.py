import pytest
from agent.tools.registry import tool, get_tool_definitions, get_tool_names, execute_tool, _TOOL_REGISTRY


@tool(name="demo_add", description="Add two numbers", parameters={"a": {"type": "number"}, "b": {"type": "number"}})
async def demo_add(a: float, b: float) -> dict:
    return {"result": a + b}


@tool(name="demo_multiply", description="Multiply two numbers")
async def demo_multiply(x: float, y: float) -> dict:
    return {"result": x * y}


def test_tool_registration():
    defs = get_tool_definitions()
    names = get_tool_names()
    assert "demo_add" in names
    assert "demo_multiply" in names
    assert any(d["function"]["name"] == "demo_add" for d in defs)


def test_tool_definition_structure():
    defs = get_tool_definitions()
    add_def = next(d for d in defs if d["function"]["name"] == "demo_add")
    assert add_def["type"] == "function"
    assert "description" in add_def["function"]
    assert "parameters" in add_def["function"]
    params = add_def["function"]["parameters"]
    assert params["type"] == "object"
    assert "a" in params["properties"]
    assert "b" in params["properties"]


@pytest.mark.asyncio
async def test_execute_tool():
    result = await execute_tool("demo_add", a=3, b=4)
    assert result == {"result": 7}


@pytest.mark.asyncio
async def test_execute_tool_multiply():
    result = await execute_tool("demo_multiply", x=5, y=6)
    assert result == {"result": 30}


@pytest.mark.asyncio
async def test_execute_unknown_tool():
    with pytest.raises(ValueError, match="Unknown tool"):
        await execute_tool("nonexistent_tool")


def test_duplicate_tool_registration():
    initial_count = len(_TOOL_REGISTRY)

    @tool(name="demo_add", description="Duplicate")
    async def duplicate_tool() -> dict:
        return {}

    assert len(_TOOL_REGISTRY) == initial_count
