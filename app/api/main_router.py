from fastapi import APIRouter
from app.api.routers import student, research, tool_discovery_test, ai_tool, main_workflow_test

api_router = APIRouter()

# Include the student router without the security dependency
api_router.include_router(
    student.router, 
    prefix="/students", 
    tags=["students"]
)

# Include the research router
api_router.include_router(
    research.router,
    prefix="/research",
    tags=["research"]
)

# Include the tool discovery test router
api_router.include_router(
    tool_discovery_test.router,
    prefix="/tool-discovery-test",
    tags=["tool-discovery-test"]
)

# Include the ai_tool router
api_router.include_router(
    ai_tool.router,
    prefix="/ai-tools",
    tags=["ai-tools"]
)

# Include the main workflow router
api_router.include_router(
    main_workflow_test.router,
    prefix="/main-workflow-test",
    tags=["main-workflow-test"]
)
