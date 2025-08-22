from langchain.tools import tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, PromptTemplate

from src.config import load_invariants
import os

INV = load_invariants()


def _anki_list_decks(limit: int):
    return [
        {"name": "French::A1", "note_count": 312},
        {"name": "EVP C1/C2", "note_count": 10452},
    ][:limit]

def _anki_list_cards(deck: str, limit: int):
    cards = [{"id": str(i), "front": f"Front {i}", "back": f"Back {i}"} for i in range(1, 50)]
    return {"deck": deck, "cards": cards[:limit]}


@tool("anki_list_decks")
def anki_list_decks(limit: int):
    """List available Anki decks with a limit on the number of decks returned."""
    # ...
    if isinstance(limit, str):
        limit = int(limit)
    decks = _anki_list_decks(limit)
    assert len(decks) <= INV.max_decks, "INV-READ-1 violated"
    return {"kind": "deck_list", "decks": decks}

@tool("anki_list_cards")
def anki_list_cards(deck: str, limit: int):
    """List cards from a specific Anki deck with a limit on the number of cards returned."""
    # ...
    if isinstance(limit, str):
        limit = int(limit)
    res = _anki_list_cards(deck, limit)
    assert len(res["cards"]) <= INV.max_cards, "INV-READ-2 violated"
    return res

SYSTEM_RULES = "You are a chat assistant for reading Anki data.\n" + "\n".join(INV.text_rules)

def build_agent(model_name: str, temperature: float = 0, verbose: bool = False) -> AgentExecutor:
    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    base_prompt = PromptTemplate.from_template("""
Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: Return the full tool output as a JSON object in fully standard JSON format, without markdown formatting.

Begin!

Question: {input}
Thought:{agent_scratchpad}
""")

    # with warnings.catch_warnings():
    #     warnings.filterwarnings("ignore", category=UserWarning, module="langsmith")
    #     base_prompt = hub.pull("hwchase17/react")

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_RULES),
        ("system", base_prompt.template),
    ])
    tools = [anki_list_decks, anki_list_cards]

    agent = create_react_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=verbose, handle_parsing_errors=True)
