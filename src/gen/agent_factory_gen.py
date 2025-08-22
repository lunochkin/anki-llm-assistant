"""
GENERATED – DO NOT EDIT

Tier-3 generated interface for agent creation.
This file provides factory functions that call Tier-2 business logic.
"""

from src.core.agent.agent_factory import AgentFactory


def create_anki_agent(model_name: str = None, temperature: float = None):
    """
    Create and configure the Anki LLM agent.
    
    Args:
        model_name: OpenAI model to use (defaults to config)
        temperature: Model temperature (defaults to config)
    
    Returns:
        Configured LangChain agent
    """
    # Create factory instance (Tier-2)
    factory = AgentFactory()
    
    # Create agent using factory (Tier-2 business logic)
    return factory.create_anki_agent(
        model_name=model_name,
        temperature=temperature
    )


def create_anki_agent_with_config(model_name: str, temperature: float):
    """
    Create agent with explicit configuration.
    
    Args:
        model_name: OpenAI model to use
        temperature: Model temperature
    
    Returns:
        Configured LangChain agent
    """
    factory = AgentFactory()
    return factory.create_anki_agent(
        model_name=model_name,
        temperature=temperature
    )


# Convenience functions for common configurations
def create_gpt4_agent():
    """Create agent with GPT-4 configuration"""
    return create_anki_agent(model_name="gpt-4o", temperature=0)


def create_gpt4_mini_agent():
    """Create agent with GPT-4o-mini configuration"""
    return create_anki_agent(model_name="gpt-4o-mini", temperature=0)


def create_test_agent():
    """Create agent for testing purposes"""
    return create_anki_agent(model_name="gpt-4o-mini", temperature=0)
