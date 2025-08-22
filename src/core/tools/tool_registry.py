class ToolRegistry:
    def __init__(self):
        self._tools = {}
        self._schemas = {}
    
    def register_tool(self, name: str, tool_func, schema: dict = None):
        """Register a tool with its schema (schema can be None for Pydantic model validation)"""
        self._tools[name] = tool_func
        self._schemas[name] = schema
    
    def get_tools(self) -> list:
        """Get all registered tools"""
        return list(self._tools.values())
    
    def get_tool_schema(self, name: str) -> dict | None:
        """Get schema for a specific tool (returns None if no schema)"""
        return self._schemas[name]
    
    def validate_tool_config(self):
        """Ensure all tools match spec requirements"""
        # Validate against your agent.spec.md requirements
        for name, schema in self._schemas.items():
            if schema is not None:  # Skip validation for tools without schemas
                self._validate_tool_against_spec(name, schema)
