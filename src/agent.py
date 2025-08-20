from langchain.tools import tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from src.config import load_invariants
import os

INV = load_invariants()

class ListDecksArgs(BaseModel):
    limit: int = Field(INV.max_decks, ge=1, le=INV.max_decks)

class ListCardsArgs(BaseModel):
    deck: str
    limit: int = Field(INV.max_cards, ge=1, le=INV.max_cards)


def _anki_list_decks(limit: int):
    return [
        {"name": "French::A1", "note_count": 312},
        {"name": "EVP C1/C2", "note_count": 10452},
    ][:limit]

def _anki_list_cards(deck: str, limit: int):
    cards = [{"id": str(i), "front": f"Front {i}", "back": f"Back {i}"} for i in range(1, 50)]
    return {"deck": deck, "cards": cards[:limit]}


@tool("anki.list_decks", args_schema=ListDecksArgs)
def anki_list_decks(limit: int = INV.max_decks):
    """List available Anki decks with a limit on the number of decks returned."""
    # ...
    decks = _anki_list_decks(limit)
    assert len(decks) <= INV.max_decks, "INV-READ-1 violated"
    return {"decks": decks}

@tool("anki.list_cards", args_schema=ListCardsArgs)
def anki_list_cards(deck: str, limit: int = INV.max_cards):
    """List cards from a specific Anki deck with a limit on the number of cards returned."""
    # ...
    res = _anki_list_cards(deck, limit)
    assert len(res["cards"]) <= INV.max_cards, "INV-READ-2 violated"
    return res

SYSTEM_RULES = "You are a chat assistant for reading Anki data.\n" + "\n".join(INV.text_rules)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_RULES),
    ("system", """When you finish tool calls, output a single JSON object:
- deck_list: {{"kind":"deck_list","decks":[{{"name":"...","note_count":123}}],"next_hint":"..."}}
- card_list: {{"kind":"card_list","deck":"...","cards":[{{"id":"...","front":"...","back":"..."}}]}}
No markdown fences, no extra text.

Available tools: {tools}
Tool names: {tool_names}"""),
    ("human", "{input}"),
    ("assistant", "{agent_scratchpad}")
])

def build_agent(model_name: str, temperature: float = 0) -> AgentExecutor:
    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    agent = create_react_agent(llm, [anki_list_decks, anki_list_cards], prompt)
    return AgentExecutor(agent=agent, tools=[anki_list_decks, anki_list_cards], verbose=False, handle_parsing_errors=True)
