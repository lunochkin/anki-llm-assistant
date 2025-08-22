from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI

from src.core.tools.tool_registry import ToolRegistry


class AgentBuilder:
    def __init__(self, config, tool_registry: ToolRegistry):
        self.config = config
        self.tool_registry = tool_registry
    
    def build_agent(self, model_name: str = None, temperature: float = None) -> AgentExecutor:
        # Use config defaults if not provided
        if model_name is None:
            model_name = self.config.model_name
        if temperature is None:
            temperature = self.config.runtime.temperature
            
        llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=self.config.openai_api_key,
        )

        # Business logic: prompt assembly
        system_rules = self._build_system_rules()
        prompt = self._build_prompt(system_rules)
        
        # Business logic: tool registration
        tools = self.tool_registry.get_tools()
        
        # Business logic: agent creation
        return self._create_react_agent(llm, prompt, tools)

    def _create_react_agent(self, llm: ChatOpenAI, prompt: ChatPromptTemplate, tools: list) -> AgentExecutor:
        agent = create_react_agent(llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=False, handle_parsing_errors=True)
    
    def _build_system_rules(self) -> str:
        # Business logic: invariant text generation
        return "You are a chat assistant for reading Anki data.\n" + \
               "\n".join(self.config.invariants.text_rules)

    def _build_prompt(self, system_rules: str) -> ChatPromptTemplate:
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
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_rules),
            ("system", base_prompt.template),
        ])
        return prompt
