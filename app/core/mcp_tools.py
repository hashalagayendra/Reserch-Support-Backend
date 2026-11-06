"""Load callable tools from the separately running MCP HTTP server."""

from fastapi import HTTPException
from langchain_core.tools import BaseTool
from research.mcp_tools import MCPConnectionError, discover_mcp_tools

from app.core.backend_config import settings

async def get_mcp_tools() -> list[BaseTool]:
    """Delegate catalog inspection to the Research package using only its URL."""
    try:
        return await discover_mcp_tools(settings.MCP_SERVER_URL)
    except MCPConnectionError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error
