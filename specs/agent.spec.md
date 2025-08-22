# Agent Specification: Anki Data Reader

## Specification References
This specification references the following files:
- **Pydantic Models**: `schemas/models.py`
- **Invariants**: `invariants.yaml`

## Overview
The Anki LLM Assistant is a chat-based interface that enables users to browse Anki decks and cards through natural language queries, with strict adherence to data access limits and privacy constraints.

## Core Capabilities
- **Deck Browsing**: List available Anki decks with note counts
- **Card Browsing**: List cards from specific decks with front/back content
- **Natural Language Interface**: Process user intent through LLM reasoning
- **Data Limiting**: Enforce strict limits on data exposure

## Tool Specifications

See `tools.yaml` for complete tool specifications including inputs, outputs, and purposes.

**Available Tools:**
- `anki_list_decks`
- `anki_list_cards`

## Agent Behavior Specification

### Prompt Engineering
**System Rules**: See `invariants.yaml` for complete business rules.

**Base Prompt Template**: See `prompts/react_agent.prompt` for the complete ReAct pattern template.

### Response Formatting
- All responses must be valid JSON
- No markdown formatting in final output
- Include tool output directly in response
- Maintain data structure integrity

### Error Handling
- **Invalid deck names**: Return error message, suggest valid decks
- **Limit violations**: Automatically clamp to maximum allowed values
- **Tool failures**: Provide clear error messages with recovery suggestions
- **Parsing errors**: Gracefully handle malformed user input

## Invariants (Business Rules)
See `invariants.yaml`.

## Tool Orchestration

### Decision Logic
1. **Deck-related queries**: Use `anki_list_decks` tool
2. **Card-related queries**: Use `anki_list_cards` tool
3. **Combined queries**: Execute tools sequentially, combine results
4. **Ambiguous queries**: Ask for clarification before proceeding

### Parameter Validation
- **Type coercion**: Convert string limits to integers when possible
- **Range validation**: Ensure limits are within allowed bounds
- **Required fields**: Validate all required parameters are present
- **Format validation**: Ensure deck names match expected patterns

## Testing Requirements

### Golden Test Scenarios
1. **Basic deck listing**: Verify limit enforcement and data structure
2. **Basic card listing**: Verify deck validation and card retrieval
3. **Limit edge cases**: Test boundary conditions (limit=1, limit=10, limit>10)
4. **Error conditions**: Test invalid deck names, malformed inputs
5. **Privacy compliance**: Verify no sensitive data leakage

### Validation Criteria
- Output matches Pydantic models from `schemas/models.py`
- All invariants are satisfied
- Tool calls use correct parameters
- Response formatting is consistent
- Error handling is graceful

## Implementation Requirements

### Tool Registration
- Tools must be registered with exact names
- Parameter validation happens at tool level
- Output validation ensures Pydantic model compliance

### Performance Requirements
- Tool execution should be fast (<100ms for typical queries)
- Caching may be implemented for frequently accessed data
- Pagination should be efficient for large datasets

### Configuration
See `implementation.yaml` for runtime configuration, model settings, and adapter specifications.
