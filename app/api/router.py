from fastapi import APIRouter
from app.api.routers import ai_tool, auth, projects
from app.core.backend_config import settings

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])

# The demos initialize AI workflows at import time; opt in for local experiments.
from app.api.routers.client_test import tool_discovery_test, main_workflow_test, openrouter_models

# Include the ai_tool router (kept directly under /ai-tools)
api_router.include_router(
    ai_tool.router,
    prefix="/ai-tools",
    tags=["ai-tools"]
)

# Include the tool discovery test router under /client-test/tool-discovery-test
if settings.ENABLE_CLIENT_TEST_ROUTES:
    api_router.include_router(tool_discovery_test.router, prefix="/client-test/tool-discovery-test", tags=["tool-discovery-test"])

# Include the openrouter models router under /client-test/models
if settings.ENABLE_CLIENT_TEST_ROUTES:
    api_router.include_router(openrouter_models.router, prefix="/client-test/models", tags=["openrouter-models"])

# Include the main workflow router under /client-test/main-workflow-test
if settings.ENABLE_CLIENT_TEST_ROUTES:
    api_router.include_router(main_workflow_test.router, prefix="/client-test/main-workflow-test", tags=["main-workflow-test"])
