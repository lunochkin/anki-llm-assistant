import json, pathlib, os
from deepdiff import DeepDiff
from dotenv import load_dotenv
from src.agent import build_agent, anki_list_decks, anki_list_cards
from src.reply_contracts import validate_reply

# Load environment variables from .env file
load_dotenv()

FIXTURES = [
    "001_list_decks"
]

def read_json(path: pathlib.Path):
    return json.loads(path.read_text())

def test_golden():
    # Get model name from environment variable, fallback to a default
    model_name = os.getenv("OPENAI_MODEL_ENV", "gpt-4o-mini")
    
    # Build agent using environment variables
    agent = build_agent(model_name=model_name, temperature=0, verbose=False)

    base = pathlib.Path("tests/golden")
    for name in FIXTURES:
        user_input = read_json(base / f"{name}.input.json")["turns"][0]["text"]
        expected = read_json(base / f"{name}.output.json")

        # Run agent
        agent_result = agent.invoke({"input": user_input})

        agent_output = json.loads(agent_result.get("output", ""))

        validate_reply(agent_output)
        
        # Compare actual output with expected output
        diff = DeepDiff(agent_output, expected)
        if diff:
            # If outputs don't match, raise an error to fail the test
            raise AssertionError(f"Output mismatch for {name}")
        
        # For now, let's just test that the tools work correctly
        # The full agent execution is complex and would need more sophisticated testing
        print(f"Test {name}: {user_input}")
        
        # Test the individual tools
        if "decks" in user_input.lower():
            deck_result = anki_list_decks.invoke({"limit": 10})
            assert "decks" in deck_result
            assert len(deck_result["decks"]) <= 10
        elif "cards" in user_input.lower():
            card_result = anki_list_cards.invoke({"deck": "French::A1", "limit": 5})
            assert "cards" in card_result
            assert len(card_result["cards"]) <= 5
            assert card_result["deck"] == "French::A1"
