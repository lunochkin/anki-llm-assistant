class ToolRegistry:
    def __init__(self):
        self._tools = {}
        self._schemas = {}
    
    def register_tool(self, name: str, tool_func, schema: dict):
        """Register a tool with its schema"""
        self._tools[name] = tool_func
        self._schemas[name] = schema
    
    def get_tools(self) -> list:
        """Get all registered tools"""
        return list(self._tools.values())
    
    def get_tool_schema(self, name: str) -> dict:
        """Get schema for a specific tool"""
        return self._schemas[name]
    
    def validate_tool_config(self):
        """Ensure all tools match spec requirements"""
        # Validate against your agent.spec.md requirements
        for name, schema in self._schemas.items():
            self._validate_tool_against_spec(name, schema)
