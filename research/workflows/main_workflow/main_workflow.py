from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.prebuilt import create_react_agent
from langchain_openrouter import ChatOpenRouter
from app.core.config import settings
from research.workflows.tool_descovery_workflow.tool_genarator import create_dynamic_api_tool
from research.workflows.main_workflow.helpers import get_recent_models, get_each_model_details, get_design_arena_benchmarks


# Array containing actual working AI tool data matching the AITool table structure.
# This data can be used to populate the ai_tools database table.
# The table structure expects: tool_title, description, argument, api_url, http_method, headers.
ai_tools_data: List[Dict[str, Any]] = [
    {
        "tool_title": "geocodeLocation",
        "description": "Geocoding API to convert location names (e.g., 'Sri Lanka') to latitude/longitude coordinates. Uses the free Open-Meteo Geocoding API which requires no API key.",
        "argument": {
            "name": {"type": "string", "description": "The location name to geocode, e.g., 'Sri Lanka', 'New York', 'Tokyo'"}
        },
        "api_url": "https://geocoding-api.open-meteo.com/v1/search?name={name}&count=1&language=en&format=json",
        "http_method": "GET",
        "headers": {
            "Accept": "application/json"
        }
    },
    {
        "tool_title": "OpenMeteoWeather",
        "description": "Fetches current weather, hourly, and daily forecasts for a given latitude and longitude. No API key required.",
        "argument": {
            "latitude": {"type": "number", "description": "Latitude of the location (e.g., 52.52)"},
            "longitude": {"type": "number", "description": "Longitude of the location (e.g., 13.41)"},
            "current_weather": {"type": "boolean", "description": "Set to true to include current weather in the response"},
            "hourly": {"type": "string", "description": "Comma-separated list of hourly variables (e.g., 'temperature_2m,relative_humidity_2m,wind_speed_10m')"},
            "daily": {"type": "string", "description": "Comma-separated list of daily variables (e.g., 'temperature_2m_max,temperature_2m_min,precipitation_sum')"},
            "timezone": {"type": "string", "description": "Timezone for the response (e.g., 'auto', 'America/New_York', 'Europe/Berlin')"},
            "forecast_days": {"type": "integer", "description": "Number of days to forecast (1-16). Default is 7."}
        },
        "api_url": "https://api.open-meteo.com/v1/forecast",
        "http_method": "GET",
        "headers": {
            "Accept": "application/json"
        }
    },
    {
        "tool_title": "getBitcoinPrice",
        "description": "Fetch current Bitcoin price and details from CoinGecko free public API (no key required)",
        "argument": {
            "currency": {"type": "string", "description": "The fiat currency to display price in, e.g. usd, eur, gbp, jpy, etc."}
        },
        "api_url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies={currency}",
        "http_method": "GET",
        "headers": {
            "Accept": "application/json"
        }
    }
]

class MainWorkFlow:
    def __init__(self, api_key: str = None, model_name: str = None, temperature: float = 0.5):
        self.api_key = api_key 
        self.model_name = model_name 
        self.temperature = temperature
        
        # 1. Create tools from the db/data array
        self.tools = [create_dynamic_api_tool(tool_dict) for tool_dict in ai_tools_data]
        
        # 2. Initialize LLM
        self.llm = ChatOpenRouter(
            model=self.model_name,
            temperature=self.temperature,
            api_key=self.api_key
        )
        
        self.mainAgent = ChatOpenRouter(
            model=self.model_name,
            temperature=self.temperature,
            api_key=self.api_key
        )

        # 3. Create agent
        self.agent_executor = create_react_agent(self.llm, tools=self.tools)

    async def test_tool_agent(self, prompt: str) -> dict:
        """
        Method to test the main workflow tool agent.
        
        Args:-
            prompt (str): The prompt to test the tool agent with.
        """
        result = await self.agent_executor.ainvoke({"messages": [("user", prompt)]})
        
        return {
            "response": result["messages"][-1].content if result and "messages" in result else "",
            "tools_available": [t.name for t in self.tools]
        }

    async def divide_task(self, task: str) -> dict:
        """
        Takes a main task and divides it into sub-tasks for sub-agents.
        Returns a structured dictionary containing sub-agent configurations.
        """
        parser = JsonOutputParser(pydantic_object=TaskDivisionResult)

        prompt = PromptTemplate(
            template="You are a Task Orchestrator Agent. Your job is to divide the user's task into logical sub-tasks for specialized sub-agents.\n"
                     "You must return the sub-agents with their specific tool assignments, system prompts, tasks, and any extra necessary details.\n"
                     "Available tools data:\n{tools_data}\n\n"
                     "User Task: {task}\n\n"
                     "{format_instructions}\n",
            input_variables=["task"],
            partial_variables={
                "format_instructions": parser.get_format_instructions(), 
                "tools_data": str([{"tool_title": t["tool_title"], "description": t["description"]} for t in ai_tools_data])
            }
        )
        chain = prompt | self.mainAgent | parser
        result = await chain.ainvoke({"task": task})
        return result

class SubAgentConfig(BaseModel):
    name: str = Field(description="Name of the sub-agent")
    task: str = Field(description="The specific sub-task assigned to this agent")
    system_prompt: str = Field(description="The system prompt defining the agent's behavior")
    tools: List[str] = Field(description="List of tool titles to be given to this agent. Must be selected from available tools.")
    extra_details: str = Field(description="Any extra necessary details or context")

class TaskDivisionResult(BaseModel):
    sub_agents: List[SubAgentConfig] = Field(description="List of sub-agents required to complete the main task")

