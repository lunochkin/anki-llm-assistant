import json
import pathlib
from typing import Dict, Any

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a JSON schema file from the specs directory"""
    # Convert relative path to absolute path - specs is in project root
    project_root = pathlib.Path(__file__).parent.parent.parent.parent
    specs_dir = project_root / "specs"
    full_path = specs_dir / schema_path
    
    # Load and parse JSON schema
    with open(full_path, 'r') as f:
        return json.load(f)
