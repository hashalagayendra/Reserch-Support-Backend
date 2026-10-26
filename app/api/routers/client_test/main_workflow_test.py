from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel, Field
from app.core.client_side_test_config import settings

router = APIRouter()


class AgentTestRequest(BaseModel):
    prompt: str = Field(
        default="What is the current weather in Berlin?", 
        description="The prompt to test the tool agent with."
    )
    api_key: Optional[str] = Field(
        default=None, 
        description="Optional OpenRouter API Key."
    )

# @router.post("/test-tool-agent")
# async def test_tool_agent(request: AgentTestRequest):
#     """
#     Endpoint to create a simple agent, bind it with tools from ai_tools_data, and execute it.
#     """
#     try:
#         from research.main import Research

        
#         key_to_use = settings.OPENROUTER_API_KEY
#         tool_discovery_model = settings.TOOL_DISCOVERY_MODEL
#         tool_discovery_temp = settings.TOOL_DISCOVERY_TEMPERATURE
#         main_workflow_model = settings.MAIN_WORKFLOW_MODEL
#         main_workflow_temp = settings.MAIN_WORKFLOW_TEMPERATURE
        
#         # 1. Initialize and configure Research object
#         print(f"API Key: {key_to_use}")
#         print(f"Tool Discovery Model: {tool_discovery_model}")
#         print(f"Tool Discovery Temperature: {tool_discovery_temp}")
#         print(f"Main Workflow Model: {main_workflow_model}")
#         print(f"Main Workflow Temperature: {main_workflow_temp}")
#         research_obj = Research()
#         research_obj.configure(
#             openRouterAPIKey=key_to_use,
#             toolDiscoveryModel=tool_discovery_model,
#             toolDiscoveryModelTemperature=tool_discovery_temp,
#             mainWorkflowModel=main_workflow_model,
#             mainWorkflowModelTemperature=main_workflow_temp
#         )
        
#         # 2. Run the agent via Research object's main_workflow
#         result = await research_obj.main_workflow.test_tool_agent(request.prompt)
        
#         return {
#             "prompt": request.prompt,
#             "response": result["response"],
#             "tools_available": result["tools_available"]
#         }
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=str(e))


# --- Example Pydantic Response Schema ---
class WeatherComparisonReport(BaseModel):
    """
    Example Pydantic structured output model.
    Intermediate agents will produce standard string data and tool calls,
    while the final concluding agent is configured to return this validated structure.
    """
    tokyo_location: str = Field(description="Geographic coordinates or location description for Tokyo")
    tokyo_weather: str = Field(description="Current weather condition and temperature for Tokyo")
    london_location: str = Field(description="Geographic coordinates or location description for London")
    london_weather: str = Field(description="Current weather condition and temperature for London")
    temperature_difference: str = Field(description="Direct comparison between Tokyo and London temperatures")
    final_summary_and_recommendation: str = Field(description="Comprehensive comparison summary and travel/clothing advice")


class MainOrchestratorTestRequest(BaseModel):
    task: str = Field(
        default="Find the geographic coordinates for Tokyo and London, retrieve their current weather and temperature forecasts using their coordinates, and provide a weather comparison summary.", 
        description="The task for the main orchestrator agent to divide into sub-agent workflows and execute."
    )

@router.post("/main-orchestrator")
async def run_main_orchestrator(request: MainOrchestratorTestRequest):
    """
    Endpoint to execute the main orchestrator agent to divide a user task into sub-agent workflows.
    Directly configured with WeatherComparisonReport response_schema for structured final output.
    """
    try:
        from research.main import Research

        key_to_use = settings.OPENROUTER_API_KEY
        tool_discovery_model = settings.TOOL_DISCOVERY_MODEL
        tool_discovery_temp = settings.TOOL_DISCOVERY_TEMPERATURE
        main_workflow_model = settings.MAIN_WORKFLOW_MODEL
        main_workflow_temp = settings.MAIN_WORKFLOW_TEMPERATURE
        
        # 1. Initialize and configure Research object
        research_obj = Research()
        research_obj.configure(
            openRouterAPIKey=key_to_use,
            toolDiscoveryModel=tool_discovery_model,
            toolDiscoveryModelTemperature=tool_discovery_temp,
            mainWorkflowModel=main_workflow_model,
            mainWorkflowModelTemperature=main_workflow_temp,
            response_schema=WeatherComparisonReport
        )
        
        # 2. Run the main orchestrator node via run() or main_orchestrator()
        result = await research_obj.run(request.task)
        
        return {
            "task": request.task,
            "structured_output": result.get("structured_output") if isinstance(result, dict) else None,
            "result": result,
            "memory_store": research_obj.main_workflow.main_orchestrator_memory_store
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


