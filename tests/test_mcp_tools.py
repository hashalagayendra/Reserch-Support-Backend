"""MCP HTTP integration and Research binding checks; no model/API calls."""

import asyncio
import socket
import subprocess
import time
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from langchain_core.tools import tool

from app.core.backend_config import settings
from app.core.mcp_tools import get_mcp_tools


@pytest.fixture
def mcp_url():
    demo = Path(__file__).resolve().parents[2] / "mcp-simple-demo"
    python = demo / ".venv/Scripts/python.exe"
    if not python.exists():
        pytest.skip("Run uv sync in mcp-simple-demo to prepare the HTTP test server.")
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    server_log = tempfile.TemporaryFile(mode="w+", encoding="utf-8")
    process = subprocess.Popen(
        [str(python), str(demo / "server.py"), "--port", str(port)],
        stdout=subprocess.DEVNULL, stderr=server_log,
    )
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if process.poll() is not None:
                pytest.fail("The MCP HTTP test server exited before startup.")
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    break
            except OSError:
                time.sleep(0.1)
        else:
            pytest.fail("The MCP HTTP test server did not become ready.")
        yield f"http://127.0.0.1:{port}/mcp"
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        server_log.seek(0)
        output = server_log.read()
        server_log.close()
        assert "Error in standalone SSE writer" not in output, output
        assert "ClosedResourceError" not in output, output


def test_http_tools_remain_callable_and_bind_to_main_agent(mcp_url, monkeypatch):
    monkeypatch.setattr(settings, "MCP_SERVER_URL", mcp_url)

    async def check():
        from research.main import Research

        @tool
        def tool_discovery_workflow(query: str) -> str:
            """Test stand-in for API discovery; never calls a model."""
            return query

        workflow_module = "research.workflows.main_workflow.main_workflow"
        with (
            patch("research.main.ErrorCorrectionSubAgent"),
            patch("research.main.ToolDiscoveryWorkflow"),
            patch(f"{workflow_module}.ChatOpenRouter"),
            patch(f"{workflow_module}.transform_tool_discovery_workflow_as_tool", return_value=tool_discovery_workflow),
            patch(f"{workflow_module}.create_react_agent") as create_agent,
        ):
            research_obj = Research()
            research_obj.configure(openRouterAPIKey="test-not-a-real-key", mcp_server_url=mcp_url)
            assert research_obj.mcp_tools == []
            assert research_obj.main_workflow is None
            await research_obj.initialize()
            await research_obj.initialize()  # Reuse the already initialized agent.
            assert create_agent.call_count == 1
            mcp_tools = research_obj.mcp_tools
            assert {t.name for t in mcp_tools} == {"greet", "get_students", "get_project_info"}
            assert research_obj.main_workflow.mcp_tools == mcp_tools
            bound_tools = create_agent.call_args.kwargs["tools"]
            assert {t.name for t in bound_tools} == {
                "greet", "get_students", "get_project_info", "tool_discovery_workflow",
            }
            # Use the actual bound tool after configure(), not just its schema.
            info = await next(t for t in bound_tools if t.name == "get_project_info").ainvoke({})
            assert "Simple MCP Demo" in str(info)
            greeting = await next(t for t in mcp_tools if t.name == "greet").ainvoke({"name": "Hashala"})
            assert "Hello, Hashala!" in str(greeting)
            # Repeated discovery and calls create/close independent sessions.
            for _ in range(3):
                refreshed = await get_mcp_tools()
                students = await next(t for t in refreshed if t.name == "get_students").ainvoke({})
                assert "Amal" in str(students)

    asyncio.run(check())


def test_unavailable_mcp_server_returns_503():
    async def check():
        with patch("research.mcp_tools.MultiServerMCPClient") as factory:
            factory.return_value.get_tools = AsyncMock(side_effect=ConnectionError("offline"))
            with pytest.raises(HTTPException) as error:
                await get_mcp_tools()
            assert error.value.status_code == 503
    asyncio.run(check())


def test_mcp_can_be_disabled(monkeypatch):
    monkeypatch.setattr(settings, "MCP_SERVER_URL", "")
    assert asyncio.run(get_mcp_tools()) == []


def test_backend_route_passes_only_mcp_url_into_research():
    from app.api.routers.client_test.main_workflow_test import router
    from research.main import Research

    @tool
    def sample_tool() -> str:
        """Return a sample fact."""
        return "sample"

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_mcp_tools] = lambda: [sample_tool]
    with patch("research.main.Research", spec=Research) as factory:
        obj = factory.return_value
        obj.run = AsyncMock(return_value={"structured_output": None})
        # main_workflow is normally created by configure().
        obj.main_workflow = SimpleNamespace(main_orchestrator_memory_store=[])
        with TestClient(app) as client:
            catalog = client.get("/mcp-tools")
            assert catalog.status_code == 200
            assert catalog.json()["tools"][0]["name"] == "sample_tool"
            result = client.post("/main-orchestrator", json={"task": "Use the sample fact"})
        assert result.status_code == 200
        assert obj.configure.call_args.kwargs["mcp_server_url"] == settings.MCP_SERVER_URL
        assert "mcp_tools" not in obj.configure.call_args.kwargs
        obj.run.assert_awaited_once_with("Use the sample fact")


def test_run_initializes_mcp_before_orchestration():
    from research.main import Research

    async def check():
        obj = Research()
        obj.tool_discovery_workflow = object()
        obj.mcp_server_url = "http://127.0.0.1:8001/mcp"
        workflow = SimpleNamespace(main_orchestrator=AsyncMock(return_value={"answer": "done"}))

        def build():
            assert obj.mcp_tools == ["loaded-tool"]
            obj.main_workflow = workflow

        with (
            patch("research.main.discover_mcp_tools", new=AsyncMock(return_value=["loaded-tool"])) as discover,
            patch.object(obj, "_build_main_workflow", side_effect=build),
        ):
            assert await obj.run("question") == {"answer": "done"}
            discover.assert_awaited_once_with(obj.mcp_server_url)
            workflow.main_orchestrator.assert_awaited_once_with("question")

    asyncio.run(check())
