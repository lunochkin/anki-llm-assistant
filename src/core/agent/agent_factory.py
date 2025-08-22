from src.core.tools.tool_registry import ToolRegistry
from src.core.tools import register_all_tools
from src.core.agent.agent_builder import AgentBuilder
from src.core.configs.config import ConfigLoader, Config

class AgentFactory:
    def __init__(self):
        self.config = self._load_config()
        self.tool_registry = self._create_tool_registry()
        self.agent_builder = self._create_agent_builder()
    
    def create_anki_agent(self, model_name: str, temperature: float = 0):
        """Create and configure the Anki LLM agent"""
        # All business logic happens here
        return self.agent_builder.build_agent(model_name, temperature)
    
    def _create_tool_registry(self) -> ToolRegistry:
        registry = ToolRegistry()
        register_all_tools(registry)
        return registry
    
    def _load_config(self) -> Config:
        return ConfigLoader().load_config()
    
    def _create_agent_builder(self) -> AgentBuilder:
        return AgentBuilder(self.config, self.tool_registry)
