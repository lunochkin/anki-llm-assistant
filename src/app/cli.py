"""
Tier-3 command-line interface for Anki LLM Assistant.

This module provides CLI commands for testing and using the assistant.
"""

import argparse
from src.app.agent_factory_gen import create_anki_agent


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Anki LLM Assistant - Chat with your Anki collection"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Start interactive chat")
    chat_parser.add_argument(
        "--model", 
        default="gpt-4o-mini", 
        help="Model to use (default: gpt-4o-mini)"
    )
    chat_parser.add_argument(
        "--temperature", 
        type=float, 
        default=0.0, 
        help="Temperature for responses (default: 0.0)"
    )
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Run test queries")
    test_parser.add_argument(
        "--model", 
        default="gpt-4o-mini", 
        help="Model to use (default: gpt-4o-mini)"
    )
    test_parser.add_argument(
        "--mode", 
        choices=["mock", "anki_connect"], 
        help="Override Anki mode (uses ANKI_MODE env var if not specified)"
    )
    
    # Service test command
    service_parser = subparsers.add_parser("test-service", help="Test Anki service directly")
    service_parser.add_argument(
        "--mode", 
        choices=["mock", "anki_connect"], 
        help="Override Anki mode (uses ANKI_MODE env var if not specified)"
    )
    
    args = parser.parse_args()
    
    if args.command == "chat":
        run_chat(args.model, args.temperature)
    elif args.command == "test":
        run_test_queries(args.model, args.mode)
    elif args.command == "test-service":
        test_anki_service(args.mode)
    else:
        parser.print_help()


def run_chat(model_name: str, temperature: float):
    """Run interactive chat mode"""
    print(f"Initializing Anki LLM Assistant with {model_name}...")
    
    try:
        agent = create_anki_agent(
            model_name=model_name,
            temperature=temperature
        )
        
        print(f"Anki LLM Assistant initialized with {model_name}")
        print("Type 'quit', 'exit', or 'q' to exit")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("You: ").strip()
                if user_input.lower() in ["quit", "exit", "q"]:
                    break
                
                if not user_input:
                    continue
                
                print("Assistant: ", end="", flush=True)
                response = agent.invoke({"input": user_input})
                print(response["output"])
                print()
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error processing query: {e}")
                print("Please try again or type 'quit' to exit.")
                
    except Exception as e:
        print(f"Failed to initialize agent: {e}")


def run_test_queries(model_name: str, mode: str = None):
    """Run predefined test queries"""
    print(f"Running test queries with {model_name}...")
    
    # Override mode if specified via CLI
    if mode:
        import os
        os.environ["ANKI_MODE"] = mode
        print(f"Using Anki mode: {mode}")
    
    try:
        agent = create_anki_agent(
            model_name=model_name,
            temperature=0
        )
        
        test_queries = [
            "What decks do I have?",
            "Show me 3 cards from my French deck",
            "How many cards are in my vocabulary deck?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\nQuery {i}: {query}")
            print("-" * 40)
            
            try:
                response = agent.invoke({"input": query})
                print(f"Response: {response['output']}")
            except Exception as e:
                print(f"Error: {e}")
                
    except Exception as e:
        print(f"Failed to initialize agent: {e}")


def test_anki_service(mode: str = None):
    """Test the Anki service directly"""
    try:
        from src.core.dependencies import get_dependency_container
        
        # Override mode if specified via CLI
        if mode:
            import os
            os.environ["ANKI_MODE"] = mode
            print(f"Overriding Anki mode to: {mode}")
        
        # Get service from dependency container (uses environment variable)
        deps = get_dependency_container()
        
        print(f"Service type: {type(deps.anki_service).__name__}")
        print(f"Using mode: {deps.config.adapters.anki_mode}")
        
        # Test decks
        print("\nTesting get_decks...")
        decks = deps.anki_service.get_decks(limit=10)  # Increased from 3 to 10
        print(f"Found {len(decks)} decks:")
        for deck in decks:
            print(f"  - {deck.name}: {deck.note_count} notes")
        
        # Test cards if decks exist
        if decks:
            first_deck = decks[0].name
            print(f"\nTesting get_cards for '{first_deck}'...")
            cards = deps.anki_service.get_cards(first_deck, limit=2)
            print(f"Found {len(cards)} cards:")
            for card in cards:
                print(f"  - Card {card.id}: {card.question[:50]}...")
        
        print("\n✅ Service test completed successfully!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Service test failed: {e}")
    finally:
        # Clean up environment variable if we set it
        if mode:
            import os
            if "ANKI_MODE" in os.environ:
                del os.environ["ANKI_MODE"]


if __name__ == "__main__":
    main()
