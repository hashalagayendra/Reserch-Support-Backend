from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel, Field
from research.workflows.main_workflow.main_workflow import  get_recent_models, get_each_model_details, get_design_arena_benchmarks
from app.core.config import settings

router = APIRouter()


class ModelsTestRequest(BaseModel):
    api_key: Optional[str] = Field(
        default=None, 
        description="Optional OpenRouter API Key."
    )

@router.post("/recent-models")
async def fetch_recent_models_api(request: ModelsTestRequest):
    """
    Endpoint to fetch models from OpenRouter API created in the last 6 months.
    """
    try:
        key_to_use = request.api_key or getattr(settings, "OPENROUTER_API_KEY", None)
        models_data = get_recent_models(api_key=key_to_use)
        
        return {
            "count": len(models_data),
            "data": models_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class EndpointsTestRequest(BaseModel):
    model_id: str = Field(
        default="z-ai/glm-5.2", 
        description="The Model ID to fetch endpoints/providers for."
    )
    api_key: Optional[str] = Field(
        default=None, 
        description="Optional OpenRouter API Key."
    )

@router.post("/each-model-details")
async def fetch_each_model_details(request: EndpointsTestRequest):
    """
    Endpoint to fetch all providers (endpoints) for a specific model.
    """
    try:
        key_to_use = request.api_key or getattr(settings, "OPENROUTER_API_KEY", None)
        endpoints_data = get_each_model_details(model_id=request.model_id, api_key=key_to_use)
        
        return {
            "model_id": request.model_id,
            "count": len(endpoints_data),
            "data": endpoints_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/design-arena-benchmarks")
async def fetch_design_arena_benchmarks():
    """
    Endpoint to fetch Design Arena benchmarks.
    """
    try:
        key_to_use = getattr(settings, "OPENROUTER_API_KEY", None)
        benchmarks_data = get_design_arena_benchmarks(api_key=key_to_use)
        
        return {
            "count": len(benchmarks_data),
            "data": benchmarks_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AgentTestRequest(BaseModel):
    prompt: str = Field(
        default="What is the current weather in Berlin?", 
        description="The prompt to test the tool agent with."
    )
    api_key: Optional[str] = Field(
        default=None, 
        description="Optional OpenRouter API Key."
    )

@router.post("/test-tool-agent")
async def test_tool_agent(request: AgentTestRequest):
    """
    Endpoint to create a simple agent, bind it with tools from ai_tools_data, and execute it.
    """
    try:
        from research.workflows.main_workflow.main_workflow import SimpleAgentWorkflow
        
        # 1. Initialize workflow
        key_to_use = request.api_key or getattr(settings, "OPENROUTER_API_KEY", None)
        workflow = SimpleAgentWorkflow(api_key=key_to_use)
        
        # 2. Run the agent
        result = await workflow.run(request.prompt)
        
        return {
            "prompt": request.prompt,
            "response": result["response"],
            "tools_available": result["tools_available"]
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

