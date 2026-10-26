from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

from app.db.session import get_db
from app.db.models import AITool, ApiKey
from app.api.deps import get_api_key

# --- SCHEMAS ---
class AIToolBaseSchema(BaseModel):
    tool_title: str
    description: Optional[str] = None
    argument: Optional[Dict[str, Any]] = None
    api_url: Optional[str] = None
    http_method: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None

class AIToolCreateRequest(AIToolBaseSchema):
    project_id: Optional[int] = None
    vector_data: Optional[List[float]] = None

class AIToolResponseSchema(AIToolBaseSchema):
    id: int
    project_id: int
    
    model_config = ConfigDict(from_attributes=True)

class AIToolSearchRequest(BaseModel):
    query_vector: List[float]
    limit: int = 2

router = APIRouter()


# store tool in database
@router.post("/", response_model=AIToolResponseSchema, status_code=status.HTTP_201_CREATED)
def create_ai_tool(
    ai_tool_in: AIToolCreateRequest, 
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key)
):
    """
    Create a new AI Tool.
    """
    if not api_key.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API Key is not associated with any project."
        )

    # Use provided project_id if valid, otherwise fallback to the API key's project
    if ai_tool_in.project_id is not None:
        if ai_tool_in.project_id != api_key.project_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API Key does not have access to this project."
            )
        target_project_id = ai_tool_in.project_id
    else:
        target_project_id = api_key.project_id

    new_tool = AITool(
        project_id=target_project_id,
        tool_title=ai_tool_in.tool_title,
        description=ai_tool_in.description,
        argument=ai_tool_in.argument,
        api_url=ai_tool_in.api_url,
        http_method=ai_tool_in.http_method,
        headers=ai_tool_in.headers,
        vector_data=ai_tool_in.vector_data
    )
    db.add(new_tool)
    try:
        db.commit()
        db.refresh(new_tool)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error. Check if the data is valid."
        )
    return new_tool


# search tools in db
@router.post("/search", response_model=List[AIToolResponseSchema])
def search_ai_tools(
    search_req: AIToolSearchRequest, 
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key)
):
    """
    Search AI Tools using vector similarity within the project associated with the API Key.
    """
    if not api_key.project_id:
        return []

    tools = db.query(AITool).filter(
        AITool.project_id == api_key.project_id
    ).order_by(
        AITool.vector_data.cosine_distance(search_req.query_vector)
    ).limit(search_req.limit).all()
    
    return tools
