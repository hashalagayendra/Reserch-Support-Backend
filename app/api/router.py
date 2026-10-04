from fastapi import APIRouter
from app.api.routers import ai_tool
from app.api.routers.client_test import student, tool_discovery_test, main_workflow_test, openrouter_models

api_router = APIRouter()

# Include the student router under /client-test/students
api_router.include_router(
    student.router, 
    prefix="/client-test/students", 
    tags=["students"]
)

# Include the ai_tool router (kept directly under /ai-tools)
api_router.include_router(
    ai_tool.router,
    prefix="/ai-tools",
    tags=["ai-tools"]
)

# Include the tool discovery test router under /client-test/tool-discovery-test
api_router.include_router(
    tool_discovery_test.router,
    prefix="/client-test/tool-discovery-test",
    tags=["tool-discovery-test"]
)

# Include the openrouter models router under /client-test/models
api_router.include_router(
    openrouter_models.router,
    prefix="/client-test/models",
    tags=["openrouter-models"]
)

# Include the main workflow router under /client-test/main-workflow-test
api_router.include_router(
    main_workflow_test.router,
    prefix="/client-test/main-workflow-test",
    tags=["main-workflow-test"]
)
