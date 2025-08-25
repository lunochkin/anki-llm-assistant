import json, pathlib, os
from deepdiff import DeepDiff
from dotenv import load_dotenv
from src.app.agent_factory_gen import create_anki_agent
from src.core.dependencies import get_dependency_container

# Load environment variables from .env file
load_dotenv()

FIXTURES = [
    "001_list_decks",
    "002_list_cards"
]

def read_json(path: pathlib.Path):
    return json.loads(path.read_text())

def test_golden():
    # Get model name from environment variable, fallback to a default
    model_name = os.getenv("OPENAI_MODEL_ENV", "gpt-4o-mini")
    
    # Build agent using new tiered architecture
    agent = create_anki_agent(model_name=model_name, temperature=0)

    base = pathlib.Path("tests/golden")
    for name in FIXTURES:
        user_input = read_json(base / f"{name}.input.json")["turns"][0]["text"]
        expected = read_json(base / f"{name}.output.json")

        # Run agent
        agent_result = agent.invoke({"input": user_input})

        agent_output = json.loads(agent_result.get("output", ""))

        # The new architecture handles validation through Pydantic models
        # No need for separate validate_reply function
        
        # Compare actual output with expected output
        diff = DeepDiff(agent_output, expected)
        if diff:
            print(diff)
            # If outputs don't match, raise an error to fail the test
            raise AssertionError(f"Output mismatch for {name}")
        
        print(f"Test {name}: {user_input}")
        
        # Test the individual tools using new architecture
        deps = get_dependency_container()
        if "decks" in user_input.lower():
            from src.core.contracts import DeckListInput
            deck_result = deps.decks_tool.list_decks(DeckListInput(limit=10))
            assert "decks" in deck_result.model_dump()
            assert len(deck_result.decks) <= 10
        elif "cards" in user_input.lower():
            from src.core.contracts import CardListInput
            card_result = deps.cards_tool.list_cards(CardListInput(deck="French::A1", limit=5))
            assert "cards" in card_result.model_dump()
            assert len(card_result.cards) <= 5
            assert card_result.deck == "French::A1"
