"""工具注册表"""
from typing import Dict, Callable, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ToolDefinition:
    name: str
    description: str
    func: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)
    category: str = "general"


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, name: str, description: str, func: Callable, parameters: dict = None, category: str = "general"):
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            func=func,
            parameters=parameters or {},
            category=category,
        )

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self, category: str = None) -> list:
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools

    def execute(self, name: str, **kwargs) -> Any:
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
        return tool.func(**kwargs)


_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry
