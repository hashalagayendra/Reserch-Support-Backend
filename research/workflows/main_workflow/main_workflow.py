from typing import List, Dict, Any
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_openrouter import ChatOpenRouter
from app.core.config import settings

@tool
def get_weather(location: str) -> str:
    """Get the current weather for a location."""
    # Hardcoded weather data for testing
    return f"The weather in {location} is 72 degrees and sunny."
from research.workflows.tool_descovery_workflow.tool_genarator import create_dynamic_api_tool
from research.workflows.main_workflow.helpers import get_recent_models, get_each_model_details, get_design_arena_benchmarks


# Array containing actual working AI tool data matching the AITool table structure.
# This data can be used to populate the ai_tools database table.
# The table structure expects: tool_title, description, argument, api_url, http_method, headers.
ai_tools_data: List[Dict[str, Any]] = [
    {
        "tool_title": "GitHub User Details",
        "description": "Provides publicly available information about someone with a GitHub account.",
        "argument": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "The handle for the GitHub user account."
                }
            },
            "required": ["username"]
        },
        "api_url": "https://api.github.com/users/{username}",
        "http_method": "GET",
        "headers": {
            "Accept": "application/vnd.github.v3+json"
        }
    },
    {
        "tool_title": "OpenMeteoWeather",
        "description": "Fetches current weather, hourly, and daily forecasts for a given latitude and longitude. No API key required.",
        "argument": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number", "description": "Latitude of the location (e.g., 52.52)"},
                "longitude": {"type": "number", "description": "Longitude of the location (e.g., 13.41)"},
                "current_weather": {"type": "boolean", "description": "Set to true to include current weather in the response"},
                "hourly": {"type": "string", "description": "Comma-separated list of hourly variables (e.g., 'temperature_2m,relative_humidity_2m,wind_speed_10m')"},
                "daily": {"type": "string", "description": "Comma-separated list of daily variables (e.g., 'temperature_2m_max,temperature_2m_min,precipitation_sum')"},
                "timezone": {"type": "string", "description": "Timezone for the response (e.g., 'auto', 'America/New_York', 'Europe/Berlin')"},
                "forecast_days": {"type": "integer", "description": "Number of days to forecast (1-16). Default is 7."}
            },
            "required": ["latitude", "longitude"]
        },
        "api_url": "https://api.open-meteo.com/v1/forecast",
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
        self.tools = [get_weather]
        
        # 2. Initialize LLM
        self.llm = ChatOpenRouter(
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
