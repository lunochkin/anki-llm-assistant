#!/usr/bin/env python3
"""
Tool Generator: Converts tool specifications to Tier-3 generated files

Usage: python src/scripts/tool_generator.py
       or: invoke generate-tools
"""

import yaml
from pathlib import Path
from typing import Dict, Any


def generate_tools():
    """Generate Tier-3 tool files from YAML specifications"""
    specs_dir = Path("specs")
    tools_spec_path = specs_dir / "tools.yaml"
    gen_dir = Path("src/app/tools")

    print("🔧 Generating Tier-3 tool files from YAML specifications...")

    if not tools_spec_path.exists():
        print(f"❌ Tools specification not found: {tools_spec_path}")
        return

    # Load tool specifications
    with open(tools_spec_path, 'r') as f:
        tools_spec = yaml.safe_load(f)

    tools = tools_spec.get('tools', {})
    if not tools:
        print("❌ No tools found in specification")
        return

    print(f"📝 Found {len(tools)} tools to generate")

    # Ensure gen directory exists
    gen_dir.mkdir(parents=True, exist_ok=True)

    # Generate individual tool files
    for tool_name, tool_spec in tools.items():
        generate_tool_file(tool_name, tool_spec, gen_dir)
        print(f"   ✅ {tool_name}")

    # Generate __init__.py
    generate_init_file(tools.keys(), gen_dir)

    # Generate register_tools.py
    generate_register_tools(tools.keys(), gen_dir)

    print(f"✅ Generated {len(tools)} tool files in {gen_dir}")


def generate_tool_file(tool_name: str, tool_spec: Dict[str, Any], gen_dir: Path):
    """Generate a single tool file"""
    
    # Extract tool information
    purpose = tool_spec.get('purpose', '')
    input_specs = tool_spec.get('input', {})
    output_spec = tool_spec.get('output', {})
    
    # Build function parameters and docstring
    params = []
    arg_docs = []
    param_names = []
    
    for param_name, param_spec in input_specs.items():
        param_type = _get_python_type(param_spec['type'])
        params.append(f"{param_name}: {param_type}")
        arg_docs.append(f"{param_name}: {param_spec['description']}")
        param_names.append(param_name)
    
    # Determine dependency container name and method name
    if tool_name == "anki_list_decks":
        dep_name = "decks_tool"
        method_name = "list_decks"
    elif tool_name == "anki_list_cards":
        dep_name = "cards_tool"
        method_name = "list_cards"
    else:
        # Fallback: remove 'anki_' prefix and use as base
        dep_name = f"{tool_name.replace('anki_', '')}_tool"
        method_name = tool_name.replace('anki_', '')
    
    # Generate the tool file content
    content = f'''"""
GENERATED – DO NOT EDIT

Tier-3 generated interface for {tool_name} tool.
This file contains tool decorators that call Tier-2 business logic.
"""

from langchain.tools import tool
from src.core.dependencies import get_dependency_container


@tool
def {tool_name}({', '.join(params)}):
    """
    {purpose}
    
    Args:
        {chr(10).join(f'        {doc}' for doc in arg_docs)}
    
    Returns:
        {output_spec.get('description', 'Tool output')}
    """
    # NO BUSINESS LOGIC - just calls Tier-2
    deps = get_dependency_container()
    result = deps.{dep_name}.{method_name}({', '.join(param_names)})
    # Convert Pydantic model to dict for LangChain compatibility
    return result.model_dump()
'''
    
    # Write the file
    output_file = gen_dir / f"{tool_name}_gen.py"
    with open(output_file, 'w') as f:
        f.write(content)


def generate_init_file(tool_names, gen_dir: Path):
    """Generate __init__.py for tools package"""
    content = """# GENERATED - DO NOT EDIT
"""
    
    for tool_name in tool_names:
        content += f"from .{tool_name}_gen import {tool_name}\n"
    
    content += "\n"
    content += f'__all__ = {list(tool_names)}\n'
    
    with open(gen_dir / "__init__.py", 'w') as f:
        f.write(content)


def generate_register_tools(tool_names, gen_dir: Path):
    """Generate register_tools.py"""
    content = '''"""
GENERATED – DO NOT EDIT

Tier-3 tool registration for Anki LLM Assistant.
This file registers decorated tools with the tool registry.
"""

import yaml
from pathlib import Path
'''
    
    # Import statements
    for tool_name in tool_names:
        content += f"from .{tool_name}_gen import {tool_name}\n"
    
    content += '''

def register_generated_tools(registry):
    """Register all Tier-3 decorated tools with the registry"""

    # Load tool specifications from Tier-1
    project_root = Path(__file__).parent.parent.parent.parent
    tools_spec_path = project_root / "specs" / "tools.yaml"

    if not tools_spec_path.exists():
        print(f"⚠️  Tools specification not found: {tools_spec_path}")
        return

    with open(tools_spec_path, 'r') as f:
        tools_spec = yaml.safe_load(f)

    # Tool mapping: name -> function
    tools = {
'''
    
    # Tool mapping
    for tool_name in tool_names:
        content += f'        "{tool_name}": {tool_name},\n'
    
    content += '''    }

    # Register only tools specified in Tier-1
    available_tools = tools_spec.get('tools', {}).keys()
    for name, func in tools.items():
        if name in available_tools:
            registry.register_tool(
                name=name,
                tool_func=func,
                schema=None  # Schema validation handled by Pydantic models
            )
'''
    
    with open(gen_dir / "register_tools.py", 'w') as f:
        f.write(content)


def _get_python_type(yaml_type: str) -> str:
    """Convert YAML type to Python type annotation"""
    type_mapping = {
        "str": "str",
        "int": "int",
        "float": "float",
        "bool": "bool",
        "list": "list",
        "dict": "dict"
    }
    return type_mapping.get(yaml_type, "Any")


if __name__ == "__main__":
    generate_tools()
    print("\n🎉 Done! Run 'invoke generate-and-test' to verify everything works.")
