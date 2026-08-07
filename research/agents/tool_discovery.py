from langchain_openrouter import ChatOpenRouter
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings

@tool
def discover_tools(query: str) -> str:
    """Discovers tools based on a user's query."""
    return f"Simulated discovery: Found a tool for '{query}'."

@tool
def add_numbers(a: int, b: int) -> int:
    """Adds two integers together and returns the sum."""
    print("run adding resalt is : ", a + b)
    return a + b

class ToolDiscoveryAgent:
    def __init__(self):
        # Initialize the LLM with OpenRouter's dedicated integration
        self.llm = ChatOpenRouter(
            model="deepseek/deepseek-v4-flash",
            temperature=0.8,
            api_key=settings.OPENROUTER_API_KEY
        )
        
        self.tools = [discover_tools, add_numbers]
        
        # Create the Agent
        self.agent_executor = create_react_agent(self.llm, self.tools)

    def run(self, query: str):
        """Helper method to run the agent with a query."""
        return self.agent_executor.invoke({"messages": [("user", query)]})
