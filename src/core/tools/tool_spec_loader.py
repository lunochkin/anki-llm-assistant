"""
Tool specification loader for Anki LLM Assistant.

This module loads tool specifications from Tier-1 and validates that
Tier-2 implementations match the specifications.
"""

import yaml
import pathlib
from specs.schemas.tool_specs import ToolsSpecification


def load_tools_specification() -> ToolsSpecification:
    """Load tool specifications from Tier-1"""
    project_root = pathlib.Path(__file__).parent.parent.parent.parent
    tools_spec_path = project_root / "specs" / "tools.yaml"
    
    if not tools_spec_path.exists():
        raise FileNotFoundError(f"Tools specification not found: {tools_spec_path}")
    
    with open(tools_spec_path, 'r') as f:
        data = yaml.safe_load(f)
    
    return ToolsSpecification(**data)


def get_available_tool_names() -> list[str]:
    """Get list of tool names that are specified in Tier-1"""
    spec = load_tools_specification()
    return list(spec.tools.keys())


def validate_tool_exists(tool_name: str) -> bool:
    """Check if a tool is specified in Tier-1"""
    available_tools = get_available_tool_names()
    return tool_name in available_tools
