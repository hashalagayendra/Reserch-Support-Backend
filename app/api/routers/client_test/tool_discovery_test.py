from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from research.workflows.tool_descovery_workflow.tool_discovery import ToolDiscoveryWorkflow
from research.db_operations.main import ToolDBClient
from app.core.client_side_test_config import settings
from app.core.backend_config import backend_settings

router = APIRouter()

# Initialize the DB Client for testing
api_key = settings.PROJECT_API_KEY or settings.DUMMY_API_KEY
base_url = f"http://127.0.0.1:8000{backend_settings.API_V1_STR}"
test_db_client = ToolDBClient(base_url=base_url, api_key=api_key)

# Initialize workflow for testing individual nodes
# We can initialize it globally here since we're just testing the pure node functions
test_workflow = ToolDiscoveryWorkflow(db_client=test_db_client)

class ToolDiscoveryStateModel(BaseModel):
    task: str | None = Field(default="Find a tool that gets the current weather in Tokyo.")
    search_queries: list[str] | None = Field(default=["weather API", "current weather"])
    local_tools_found: list[dict] | None = Field(default=[{"tool_title": "get_current_weather", "description": "Gets weather data."}])
    is_sufficient: bool | None = Field(default=False)
    missing_capabilities: list[str] | None = Field(default=["Unable to find a tool for translating Japanese to English."])
    web_tools_found: list[dict] | None = Field(default=[{
        "tool_title": "WebTool_cat_facts",
        "description": "An excellent tool found on the web that provides: random cat facts",
        "argument": {"max_length": {"type": "integer", "description": "Maximum length of the cat fact"}},
        "api_url": "https://catfact.ninja/fact",
        "http_method": "GET",
        "headers": {"Accept": "application/json"}
    }])
    tested_tools: list[dict] | None = Field(default=[{
        "tool_title": "WebTool_cat_facts",
        "description": "An excellent tool found on the web that provides: random cat facts",
        "argument": {"max_length": {"type": "integer", "description": "Maximum length of the cat fact"}},
        "api_url": "https://catfact.ninja/fact",
        "http_method": "GET",
        "headers": {"Accept": "application/json"},
        "tested_and_passed": True
    }])
    final_answer: str | None = Field(default="I found the weather tool.")

@router.post("/analyze_task")
def test_analyze_task(state: ToolDiscoveryStateModel):
    return test_workflow.node_analyze_task(state.model_dump())

@router.post("/explore_db")
def test_explore_db(state: ToolDiscoveryStateModel):
    return test_workflow.node_explore_db(state.model_dump())

@router.post("/evaluate_tools")
def test_evaluate_tools(state: ToolDiscoveryStateModel):
    return test_workflow.node_evaluate_tools(state.model_dump())

@router.post("/web_search")
def test_web_search(state: ToolDiscoveryStateModel):
    return test_workflow.node_web_search(state.model_dump())

@router.post("/test_tool")
def test_test_tool(state: ToolDiscoveryStateModel):
    return test_workflow.node_test_tool(state.model_dump())

@router.post("/store_tool")
def test_store_tool(state: ToolDiscoveryStateModel):
    return test_workflow.node_store_tool(state.model_dump())

@router.post("/final_answer")
def test_final_answer(state: ToolDiscoveryStateModel):
    return test_workflow.node_final_answer(state.model_dump())

class FullDiscoveryQueryRequest(BaseModel):
    query: str = Field(default="Find a tool to get the current weather in Tokyo.")

@router.post("/run_fully_tool_discovery_workflow")
async def run_fully_tool_discovery_workflow(request: FullDiscoveryQueryRequest):
    """
    Runs the complete end-to-end Tool Discovery Workflow with the given task query.
    """
    from fastapi import HTTPException
    from research.main import Research
    
    try:
        research_agent = Research()
        research_agent.configure(
            openRouterAPIKey=settings.OPENROUTER_API_KEY,
            toolDiscoveryModel=settings.TOOL_DISCOVERY_MODEL,
            toolDiscoveryModelTemperature=settings.TOOL_DISCOVERY_TEMPERATURE,
            projectApiKey=settings.PROJECT_API_KEY
        )
        result = await research_agent.tool_discovery_workflow.tool_discovery_workflow_run(request.query)
        
        final_response = result.get("final_answer", "")
        return {
            "response": final_response,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

