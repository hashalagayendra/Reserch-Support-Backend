from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from app.db.session import get_db
from app.db.models import AITool, ApiKey
from app.schemas.ai_tool import AIToolCreate, AIToolResponse, ToolSearchRequest
from app.api.deps import get_api_key

router = APIRouter()

@router.post("/", response_model=AIToolResponse, status_code=status.HTTP_201_CREATED)
def create_ai_tool(
    ai_tool_in: AIToolCreate, 
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key)
):
    """
    Create a new AI Tool.
    """
    if not api_key.projects:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API Key is not associated with any projects."
        )

    # Use provided project_id if valid, otherwise fallback to the API key's first project
    if ai_tool_in.project_id is not None:
        if ai_tool_in.project_id not in [p.id for p in api_key.projects]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API Key does not have access to this project."
            )
        target_project_id = ai_tool_in.project_id
    else:
        target_project_id = api_key.projects[0].id

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



@router.post("/search", response_model=List[AIToolResponse])
def search_ai_tools(
    search_req: ToolSearchRequest, 
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key)
):
    """
    Search AI Tools using vector similarity.
    """
    # Ensure the user can only search within projects they have access to
    allowed_project_ids = [p.id for p in api_key.projects]
    if not allowed_project_ids:
        return []

    tools = db.query(AITool).filter(
        AITool.project_id.in_(allowed_project_ids)
    ).order_by(
        AITool.vector_data.cosine_distance(search_req.query_vector)
    ).limit(search_req.limit).all()
    
    return tools
