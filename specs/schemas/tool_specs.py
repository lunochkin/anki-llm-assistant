"""
Tool specification models for Anki LLM Assistant.

These models define the structure of tool specifications and avoid duplication
with the main data models in models.py.
"""

from typing import Dict
from pydantic import BaseModel


class ToolInputSpec(BaseModel):
    type: str
    description: str
    max_value: str = None  # Reference to invariants


class ToolOutputSpec(BaseModel):
    model: str  # Reference to model name in models.py
    description: str


class ToolSpec(BaseModel):
    name: str
    purpose: str
    input: Dict[str, ToolInputSpec]
    output: ToolOutputSpec


class ToolsSpecification(BaseModel):
    tools: Dict[str, ToolSpec]
