"""
Dependency container for Anki LLM Assistant.

This module creates and manages all the dependencies needed by the system,
ensuring proper initialization and dependency injection.
"""

from src.core.configs.config import load_config
from src.core.services.anki_service import AnkiService
from src.core.validators.input_validator import InputValidator
from src.core.validators.invariant_checker import InvariantChecker
from src.core.services.response_formatter import ResponseFormatter
from src.core.tools.decks_tool import DecksTool
from src.core.tools.cards_tool import CardsTool
from src.core.tools.tool_registry import ToolRegistry


class DependencyContainer:
    """Container for managing all system dependencies"""
    
    def __init__(self):
        self.config = load_config()
        self._create_services()
        self._create_tools()
        self._create_tool_registry()
    
    def _create_services(self):
        """Create all service instances"""
        self.anki_service = AnkiService()
        self.response_formatter = ResponseFormatter()
    
    def _create_validators(self):
        """Create all validator instances"""
        self.input_validator = InputValidator()
        self.invariant_checker = InvariantChecker()
    
    def _create_tools(self):
        """Create all tool instances with proper dependencies"""
        self._create_validators()
        
        self.decks_tool = DecksTool(
            anki_service=self.anki_service,
            validator=self.input_validator,
            invariant_checker=self.invariant_checker,
            response_formatter=self.response_formatter
        )
        
        self.cards_tool = CardsTool(
            anki_service=self.anki_service,
            validator=self.input_validator,
            invariant_checker=self.invariant_checker,
            response_formatter=self.response_formatter
        )
    
    def _create_tool_registry(self):
        """Create and populate the tool registry"""
        self.tool_registry = ToolRegistry()
        # Tool registry will be populated by register_all_tools() call
    
    def get_tool_registry(self) -> ToolRegistry:
        """Get the populated tool registry"""
        return self.tool_registry
    
    def get_config(self):
        """Get the configuration"""
        return self.config


# Global dependency container instance
_dependency_container = None


def get_dependency_container() -> DependencyContainer:
    """Get the global dependency container instance"""
    global _dependency_container
    if _dependency_container is None:
        _dependency_container = DependencyContainer()
    return _dependency_container


def get_tool_registry() -> ToolRegistry:
    """Get the tool registry from the dependency container"""
    return get_dependency_container().get_tool_registry()


def get_config():
    """Get the configuration from the dependency container"""
    return get_dependency_container().get_config()
