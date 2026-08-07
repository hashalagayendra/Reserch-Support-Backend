from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from research.main import Research
from app.core.config import settings

router = APIRouter()
# Initialize the research agent once to be reused across requests
research_agent = Research()

class QueryRequest(BaseModel):
    query: str

@router.post("/discover")
async def run_discovery(request: QueryRequest):
    """
    Endpoint to run the tool discovery agent with a given query.
    """
    try:
       research_agent = Research()
       research_agent.configure(
           openRouterAPIKey=settings.OPENROUTER_API_KEY,
           toolDiscoveryModel=settings.TOOL_DISCOVERY_MODEL,
           toolDiscoveryModelTemperature=settings.TOOL_DISCOVERY_TEMPERATURE,
           projectApiKey=settings.PROJECT_API_KEY
       )
       result = await research_agent.run(request.query)
       
       # Extract the final response message from the agent's output
       messages = result.get("messages", [])
       if messages:
           final_response = messages[-1].content
           return {"response": final_response}
            
       return {"response": str(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
