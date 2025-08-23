#!/usr/bin/env python3
"""
Schema Generator: Converts YAML schemas to Pydantic models

Usage: python src/scripts/schema_generator.py
       or: invoke generate-models
"""
import yaml
from pathlib import Path

def generate_models():
    """Generate Pydantic models from YAML schemas"""
    specs_dir = Path("specs/schemas")
    output_file = Path("src/core/generated/models.py")

    print("🔧 Generating Pydantic models from YAML schemas...")

    if not specs_dir.exists():
        print(f"❌ Schema directory not found: {specs_dir}")
        return

    # Find schema files
    schema_files = list(specs_dir.glob("*.schema.yaml"))
    if not schema_files:
        print(f"❌ No schema files found in {specs_dir}")
        return

    print(f"📝 Found {len(schema_files)} schema files")

    # Generate models from all schema files
    models = []
    for schema_file in schema_files:
        schema = yaml.safe_load(open(schema_file))
        class_name = schema_file.stem.replace('.schema', '').replace('_', ' ').title().replace(' ', '')
        models.append((class_name, schema))
        print(f"   ✅ {class_name}")

    # Write models to file
    with open(output_file, 'w') as f:
        f.write("# GENERATED - DO NOT EDIT\n")
        f.write("from __future__ import annotations\n")
        f.write("from pydantic import BaseModel\n")
        f.write("from typing import Optional, List, Literal, Any\n\n")

        # Write all models
        for class_name, schema in models:
            f.write(f"class {class_name}(BaseModel):\n")
            properties = schema.get('properties', {})
            required = schema.get('required', [])

            for prop_name, prop_schema in properties.items():
                field_type = _get_type(prop_schema)
                if prop_name in required:
                    f.write(f"    {prop_name}: {field_type}\n")
                else:
                    default = prop_schema.get('default')
                    if default is not None:
                        f.write(f"    {prop_name}: Optional[{field_type}] = {default}\n")
                    else:
                        f.write(f"    {prop_name}: Optional[{field_type}] = None\n")
            f.write("\n")

    # Update __init__.py
    all_models = [name for name, _ in models]
    with open(Path("src/core/generated/__init__.py"), 'w') as f:
        f.write("# GENERATED - DO NOT EDIT\n")
        f.write("from .models import " + ", ".join(all_models) + "\n\n")
        f.write(f'__all__ = {all_models}\n')

    print(f"✅ Generated {len(all_models)} models in {output_file}")

def _get_type(schema):
    """Get Pydantic type from schema"""
    schema_type = schema.get('type')

    if schema_type == 'string':
        if 'enum' in schema:
            return f"Literal[{', '.join(repr(v) for v in schema['enum'])}]"
        return "str"
    elif schema_type == 'integer':
        return "int"
    elif schema_type == 'number':
        return "float"
    elif schema_type == 'boolean':
        return "bool"
    elif schema_type == 'array':
        items = schema.get('items', {})
        if '$ref' in items:
            ref_name = Path(items['$ref']).stem.replace('.schema', '').replace('_', ' ').title().replace(' ', '')
            return f"List['{ref_name}']"
        else:
            return f"List[{_get_type(items)}]"
    elif '$ref' in schema:
        ref_name = Path(schema['$ref']).stem.replace('.schema', '').replace('_', ' ').title().replace(' ', '')
        return f"'{ref_name}'"

    return "Any"

if __name__ == "__main__":
    generate_models()
    print("\n🎉 Done! Run 'invoke generate-and-test' to verify everything works.")