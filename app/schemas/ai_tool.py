from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List

class AIToolBase(BaseModel):
    tool_title: str
    description: Optional[str] = None
    argument: Optional[Dict[str, Any]] = None
    api_url: Optional[str] = None
    http_method: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None

class AIToolCreate(AIToolBase):
    project_id: Optional[int] = None
    vector_data: Optional[List[float]] = None



class AIToolResponse(AIToolBase):
    id: int
    project_id: int
    
    model_config = ConfigDict(from_attributes=True)

class ToolSearchRequest(BaseModel):
    query_vector: List[float]
    limit: int = 2
