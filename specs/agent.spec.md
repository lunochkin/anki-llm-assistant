# Agent Specification: Anki Data Reader

## Specification References
This specification references the following files:
- **Pydantic Models**: `schemas/models.py`
- **Invariants**: `invariants.yaml`

## Overview
The Anki LLM Assistant is a chat-based interface that enables users to browse Anki decks and cards through natural language queries, with strict adherence to data access limits and privacy constraints.

## Tool Specifications
See `tools.yaml` for complete tool specifications including inputs, outputs, and purposes.

## Agent Behavior Specification

### Prompt Engineering
**System Rules**: See `invariants.yaml` for complete business rules.

**Base Prompt Template**: See `prompts/react_agent.prompt` for the complete ReAct pattern template.

## Testing Requirements
See `tests/test_golden.py` for golden test scenarios.

## Configuration
See `implementation.yaml` for runtime configuration, model settings, and adapter specifications.
