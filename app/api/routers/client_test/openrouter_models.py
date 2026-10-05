from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel, Field
from research.workflows.main_workflow.utility import (
    get_recent_models,
    get_each_model_details,
    get_design_arena_benchmarks,
)
from app.core.client_side_test_config import settings

router = APIRouter()


# --- REQUEST SCHEMAS ---

class RecentModelsRequest(BaseModel):
    api_key: Optional[str] = Field(
        default=None, 
        description="Optional OpenRouter API Key. If omitted, the server configured key will be used."
    )


class ModelDetailsRequest(BaseModel):
    model_id: str = Field(
        default="z-ai/glm-5.2", 
        description="The Model ID to fetch endpoints/providers for (e.g. 'z-ai/glm-5.2')."
    )
    api_key: Optional[str] = Field(
        default=None, 
        description="Optional OpenRouter API Key. If omitted, the server configured key will be used."
    )


# --- ROUTE HANDLERS ---

@router.post(
    "/recent-models",
    summary="Fetch Recent OpenRouter Models",
    description="Fetch AI models from the OpenRouter API released within the last 6 months, including pricing, context limits, and architecture details.",
    response_description="A list of recently released models with total count."
)
async def fetch_recent_models(request: RecentModelsRequest):
    """
    Fetch models from OpenRouter API created within the last 6 months.
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


@router.post(
    "/each-model-details",
    summary="Fetch Model Endpoint & Provider Details",
    description="Retrieve all provider endpoints, per-token pricing, and context limits for a specific model ID (e.g. 'z-ai/glm-5.2').",
    response_description="Provider and endpoint details for the requested model ID."
)
async def fetch_model_details(request: ModelDetailsRequest):
    """
    Fetch all providers, endpoints, and specifications for a specific model ID.
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


@router.post(
    "/design-arena-benchmarks",
    summary="Fetch Design Arena Benchmarks",
    description="Fetch Design Arena leaderboard benchmarks and evaluation ratings across leading LLMs.",
    response_description="List of benchmark rankings and performance metrics."
)
async def fetch_arena_benchmarks():
    """
    Fetch Design Arena benchmarks and ratings for models.
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
