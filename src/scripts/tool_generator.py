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
    input_spec = tool_spec.get('input', {})
    output_spec = tool_spec.get('output', {})
    
    # Load input schema to get parameter information
    input_schema_name = input_spec.get('schema')
    if not input_schema_name:
        raise ValueError(f"Tool {tool_name} missing input schema")
    
    input_schema = load_schema(input_schema_name)
    if not input_schema:
        raise ValueError(f"Could not load input schema {input_schema_name} for tool {tool_name}")
    
    # Build function parameters and docstring from schema
    input_model_name = input_schema.get('title', input_schema_name)
    properties = input_schema.get('properties', {})
    param_names = list(properties.keys())
    
    # Generate parameter documentation for LLM understanding
    arg_docs = []
    for param_name, param_spec in properties.items():
        param_type = _get_python_type_from_schema(param_spec)
        description = param_spec.get('description', 'Parameter')
        arg_docs.append(f"{param_name} ({param_type}): {description}")
    
    # Determine dependency container name and method name
    # Remove 'anki_' prefix and use consistent naming pattern
    base_name = tool_name.replace('anki_', '')
    # Convert snake_case to singular form for dependency name
    if base_name.startswith('list_'):
        dep_name = f"{base_name[5:]}_tool"  # Remove 'list_' prefix
        method_name = base_name
    else:
        dep_name = f"{base_name}_tool"
        method_name = base_name
    
    # Generate the tool file content
    content = f'''"""
GENERATED – DO NOT EDIT

Tier-3 generated interface for {tool_name} tool.
This file contains tool decorators that call Tier-2 business logic.
"""

from langchain.tools import tool
from src.core.dependencies import get_dependency_container
from src.core.generated.models import {input_model_name}


@tool
def {tool_name}(input_data: str):
    """
    {purpose}
    
    Expected input parameters:
        {chr(10).join(f'        {doc}' for doc in arg_docs)}
    
    Args:
        input_data: JSON string containing the input parameters
    
    Returns:
        {output_spec.get('description', 'Tool output')}
    """
    # NO BUSINESS LOGIC - just calls Tier-2
    import json
    
    deps = get_dependency_container()
    
    # Parse JSON string and create Pydantic model instance
    input_dict = json.loads(input_data)
    input_model = {input_model_name}(**input_dict)
    
    result = deps.{dep_name}.{method_name}(input_model)
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


def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a schema file by name"""
    try:
        schema_file = Path(__file__).parent.parent.parent / 'specs' / 'schemas' / f'{schema_name}.schema.yaml'
        if not schema_file.exists():
            print(f"⚠️  Schema file not found: {schema_file}")
            return None
            
        with open(schema_file, 'r') as f:
            schema = yaml.safe_load(f)
            if not schema or 'properties' not in schema:
                print(f"⚠️  Invalid schema file {schema_name}: missing properties")
                return None
            return schema
    except Exception as e:
        print(f"❌ Error loading schema {schema_name}: {e}")
        return None


def _get_python_type_from_schema(param_spec: Dict[str, Any]) -> str:
    """Convert JSON Schema type to Python type annotation"""
    schema_type = param_spec.get('type', 'string')
    type_mapping = {
        'string': 'str',
        'integer': 'int',
        'number': 'float',
        'boolean': 'bool',
        'array': 'list',
        'object': 'dict',
    }
    return type_mapping.get(schema_type, 'Any')





if __name__ == "__main__":
    generate_tools()
    print("\n🎉 Done! Run 'invoke generate-and-test' to verify everything works.")
