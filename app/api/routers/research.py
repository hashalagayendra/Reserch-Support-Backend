from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from research.main import Research

router = APIRouter()
# Initialize the research agent once to be reused across requests
research_agent = Research()

class QueryRequest(BaseModel):
    query: str

@router.post("/discover")
def run_discovery(request: QueryRequest):
    """
    Endpoint to run the tool discovery agent with a given query.
    """
    try:
       research_agent = Research()

       result = research_agent.run()
       
       print("hi")
            
       return {"response": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
