"""
Prompt loader utility for Anki LLM Assistant.

This module loads prompt templates from Tier-1 (specs) for use in Tier-2 code.
"""

import pathlib


def load_prompt_template(prompt_name: str) -> str:
    """Load a prompt template from the specs directory"""
    project_root = pathlib.Path(__file__).parent.parent.parent.parent
    prompts_dir = project_root / "specs" / "prompts"
    prompt_path = prompts_dir / f"{prompt_name}.prompt"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {prompt_path}")
    
    with open(prompt_path, 'r') as f:
        return f.read().strip()
