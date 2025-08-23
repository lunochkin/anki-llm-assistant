def register_all_tools(registry):
    """Register all tools with the registry"""
    # Import and call Tier-3 tool registration
    from src.app.tools.register_tools import register_generated_tools
    register_generated_tools(registry)
