"""
GENERATED – DO NOT EDIT

Tier-3 main entry point for Anki LLM Assistant.
This file provides the main interface for users to create and use agents.
"""

import os
from src.gen.agent_factory_gen import create_anki_agent


def main():
    """Main entry point for the Anki LLM Assistant"""
    # Create agent using Tier-3 interface (which calls Tier-2)
    agent = create_anki_agent()
    
    # Example usage
    print("Anki LLM Assistant initialized!")
    print("Use the agent to interact with your Anki collection.")
    
    return agent


def create_agent_with_env_config():
    """Create agent using environment variables"""
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("OPENAI_TEMPERATURE", "0"))
    
    return create_anki_agent(
        model_name=model_name,
        temperature=temperature
    )


if __name__ == "__main__":
    agent = main()
    # The agent is now ready to use
    # You can add interactive loop or API endpoints here
