"""
Tier-3 command-line interface for Anki LLM Assistant.

This file provides CLI access to the agent functionality.
"""

import argparse
import sys
from src.app.agent_factory_gen import create_anki_agent, create_gpt4_agent, create_test_agent


def create_cli_parser():
    """Create command-line argument parser"""
    parser = argparse.ArgumentParser(
        description="Anki LLM Assistant - Chat with your Anki collection"
    )
    
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini)"
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Model temperature (default: 0.0)"
    )
    
    parser.add_argument(
        "--preset",
        choices=["default", "gpt4", "test"],
        default="default",
        help="Preset configuration (default: default)"
    )
    
    parser.add_argument(
        "--query",
        help="Single query to run (optional)"
    )
    
    return parser


def main_cli():
    """Main CLI entry point"""
    parser = create_cli_parser()
    args = parser.parse_args()
    
    try:
        # Create agent based on preset or arguments
        if args.preset == "gpt4":
            agent = create_gpt4_agent()
        elif args.preset == "test":
            agent = create_test_agent()
        else:
            agent = create_anki_agent(
                model_name=args.model,
                temperature=args.temperature
            )
        
        print(f"Anki LLM Assistant initialized with {args.model}")
        
        # Handle single query if provided
        if args.query:
            print(f"Running query: {args.query}")
            result = agent.invoke({"input": args.query})
            print(f"Result: {result}")
        else:
            print("Agent ready. Use --query to run a single command.")
            print("For interactive mode, run without --query")
        
        return agent
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main_cli()
