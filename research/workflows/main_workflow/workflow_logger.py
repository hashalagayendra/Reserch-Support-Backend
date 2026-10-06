"""
Workflow Logger for Main Workflow & Tool Discovery.

Provides visual, rich-formatted terminal logging for:
- Orchestrator planning & tool discovery workflows
- Layer-by-layer sub-agent topology and bindings
- Dynamic API tool requests, responses, HTTP status, and latency (ms)
- Sub-agent execution steps, tool invocations, and formatted output cards
- Layer execution tables with status badges and final synthesized responses
"""

import sys
import json
import time
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.syntax import Syntax
from rich import box

# Ensure Windows terminal handles UTF-8 emojis and box characters cleanly
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console()


class WorkflowLogger:
    """Centralized visual terminal logger for the entire workflow execution lifecycle."""

    # =========================================================================
    # 1. ORCHESTRATOR PLANNING LOGS
    # =========================================================================

    @classmethod
    def log_orchestrator_start(cls, task: str) -> None:
        """Visual panel for the start of orchestrator planning."""
        console.print()
        console.print(
            Panel(
                f"[bold white]{task}[/bold white]",
                title="[bold yellow]🎯 TASK ORCHESTRATOR PLANNING[/bold yellow]",
                subtitle="[dim]Analyzing requirements & dividing task into sequential layers[/dim]",
                border_style="yellow",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )

    @classmethod
    def log_orchestrator_result(
        cls,
        task: str,
        result: Any,
        orchestrator_res: Optional[Dict[str, Any]] = None
    ) -> None:
        """Visual display of tool calls made and structured plan table or syntax JSON."""
        # 1. Log any tool calls made by the orchestrator (e.g. tool_discovery_workflow)
        if orchestrator_res:
            messages = orchestrator_res.get("messages", [])
            tool_calls_made = []
            for msg in messages:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tc_name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", str(tc))
                        tc_args = tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {})
                        tool_calls_made.append((tc_name, tc_args))

            if tool_calls_made:
                table = Table(
                    title="🔧 Autonomous Tool Calls (Orchestrator)",
                    border_style="cyan",
                    box=box.ROUNDED,
                    show_header=True,
                    header_style="bold cyan"
                )
                table.add_column("Discovered Tool / Workflow", style="bold yellow", width=28)
                table.add_column("Arguments Sent", style="white")
                for name, args in tool_calls_made:
                    table.add_row(name, json.dumps(args, ensure_ascii=False))
                console.print(table)
                console.print()

        # 2. Try to render a structured Plan Table if 'layers' is present
        layers = []
        if isinstance(result, dict):
            layers = result.get("layers", [])
        elif hasattr(result, "layers"):
            layers = getattr(result, "layers", [])

        if layers:
            plan_table = Table(
                title=f"📋 Execution Plan Topology: \"{task[:55]}...\"",
                border_style="green",
                box=box.ROUNDED,
                show_lines=True,
                header_style="bold green",
                expand=True
            )
            plan_table.add_column("Layer", style="bold yellow", justify="center", width=8)
            plan_table.add_column("Sub-Agent", style="bold cyan", width=22)
            plan_table.add_column("Model", style="magenta", width=26)
            plan_table.add_column("Assigned Task", style="white")
            plan_table.add_column("Tools Bound", style="bright_blue", width=22)

            for layer in layers:
                if isinstance(layer, dict):
                    layer_num = str(layer.get("layer_number", "?"))
                    sub_agents = layer.get("sub_agents", [])
                else:
                    layer_num = str(getattr(layer, "layer_number", "?"))
                    sub_agents = getattr(layer, "sub_agents", [])

                for idx, agent in enumerate(sub_agents):
                    if isinstance(agent, dict):
                        agent_name = agent.get("name", "SubAgent")
                        agent_model = agent.get("model_name", "N/A")
                        agent_task = agent.get("task", "")
                        agent_tools = agent.get("tools", [])
                    else:
                        agent_name = getattr(agent, "name", "SubAgent")
                        agent_model = getattr(agent, "model_name", "N/A")
                        agent_task = getattr(agent, "task", "")
                        agent_tools = getattr(agent, "tools", [])

                    tool_names = []
                    for t in agent_tools:
                        if isinstance(t, dict):
                            tool_names.append(t.get("tool_title", "tool"))
                        elif hasattr(t, "tool_title"):
                            tool_names.append(t.tool_title)
                        elif hasattr(t, "name"):
                            tool_names.append(t.name)
                        else:
                            tool_names.append(str(t))

                    tools_str = ", ".join(tool_names) if tool_names else "[dim]None[/dim]"
                    layer_label = f"Layer {layer_num}" if idx == 0 else ""
                    plan_table.add_row(layer_label, agent_name, agent_model, agent_task, tools_str)

            console.print(plan_table)
            console.print()
        else:
            try:
                json_str = json.dumps(result, indent=2, ensure_ascii=False)
                syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
                console.print(
                    Panel(
                        syntax,
                        title="[bold green]🎯 Task Orchestrator Result (JSON)[/bold green]",
                        border_style="green",
                        box=box.ROUNDED,
                        padding=(1, 2),
                    )
                )
            except Exception:
                console.print(Panel(str(result), title="[bold green]Orchestrator Result[/bold green]", border_style="green"))

    # =========================================================================
    # 2. ARCHITECTURE TOPOLOGY LOGS
    # =========================================================================

    @classmethod
    def log_executable_layers(cls, executable_layers_list: List[Any]) -> None:
        """Visual tree diagram of generated executable layers and sub-agents."""
        tree = Tree(f"[bold cyan]🚀 Compiled Multi-Agent Architecture ({len(executable_layers_list)} Layers)[/bold cyan]")
        for layer in executable_layers_list:
            layer_num = getattr(layer, "layer_number", "?")
            sub_agents = getattr(layer, "sub_agents", [])
            layer_branch = tree.add(f"[bold yellow]📦 Layer {layer_num}[/bold yellow] [dim]({len(sub_agents)} Parallel Sub-Agents)[/dim]")
            for idx, agent in enumerate(sub_agents, 1):
                agent_tools = getattr(agent, "tools", []) or []
                tool_names = [t.name for t in agent_tools if hasattr(t, "name")]
                tools_str = ", ".join(tool_names) if tool_names else "[dim]None[/dim]"
                is_ready = getattr(agent, "executor", None) is not None
                status = "[green]Ready ✅[/green]" if is_ready else "[red]Failed ❌[/red]"

                agent_node = layer_branch.add(
                    f"[bold green]Agent #{idx}: {getattr(agent, 'name', 'SubAgent')}[/bold green] "
                    f"[dim]({getattr(agent, 'model_name', 'N/A')})[/dim] - {status}"
                )
                agent_node.add(f"[bold white]Task:[/bold white] {getattr(agent, 'task', 'N/A')}")
                agent_node.add(f"[bold blue]Available Tools ({len(tool_names)}):[/bold blue] {tools_str}")

        console.print(
            Panel(
                tree,
                title="[bold bright_blue]ARCHITECTURE & AGENT TOPOLOGY[/bold bright_blue]",
                border_style="bright_blue",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        console.print()

    # =========================================================================
    # 3. LAYER LIFECYCLE LOGS
    # =========================================================================

    @classmethod
    def log_layer_start(
        cls,
        layer_num: int,
        sub_agent_count: Optional[int] = None,
        sub_agents: Optional[List[Any]] = None
    ) -> None:
        """Visual divider and table for execution layer start."""
        agents = sub_agents or []
        count = len(agents) if agents else (sub_agent_count or 0)

        console.print()
        console.rule(
            f"[bold yellow]▶️  STARTING LAYER {layer_num} ({count} Parallel Sub-Agents)[/bold yellow]",
            style="yellow",
        )
        if agents:
            queue_table = Table(
                title=f"Parallel Execution Queue (Layer {layer_num})",
                box=box.SIMPLE_HEAVY,
                border_style="yellow",
                header_style="bold yellow",
                show_header=True,
                expand=True
            )
            queue_table.add_column("Agent Name", style="bold cyan", width=22)
            queue_table.add_column("Assigned Task", style="white")
            queue_table.add_column("Tools Ready", style="bright_blue", width=22)

            for ag in agents:
                name = getattr(ag, "name", "SubAgent") if not isinstance(ag, dict) else ag.get("name", "SubAgent")
                task = getattr(ag, "task", "") if not isinstance(ag, dict) else ag.get("task", "")
                tools = getattr(ag, "tools", []) if not isinstance(ag, dict) else ag.get("tools", [])
                t_names = [t.name for t in tools if hasattr(t, "name")] if tools else []
                queue_table.add_row(name, task, ", ".join(t_names) if t_names else "[dim]None[/dim]")

            console.print(queue_table)
        console.print()

    @classmethod
    def log_layer_complete(
        cls,
        layer_num: int,
        layer_results: Optional[List[Any]] = None,
        result_count: Optional[int] = None
    ) -> None:
        """Visual table summary of all sub-agents in a completed layer."""
        results = layer_results or []
        if results:
            success_count = sum(1 for r in results if getattr(r, "status", "") == "success")
            error_count = len(results) - success_count

            summary_table = Table(
                title=f"📦 Layer {layer_num} Completed Summary ({len(results)} Agents)",
                border_style="bright_blue",
                box=box.ROUNDED,
                header_style="bold bright_blue",
                show_header=True,
                expand=True
            )
            summary_table.add_column("Sub-Agent", style="bold cyan", width=20)
            summary_table.add_column("Status", justify="center", width=14)
            summary_table.add_column("Task", style="dim", max_width=34)
            summary_table.add_column("Output Preview", style="white")

            for r in results:
                name = getattr(r, "name", "SubAgent")
                status = getattr(r, "status", "unknown")
                task = getattr(r, "task", "")
                resp = str(getattr(r, "response", "")).strip()
                preview = resp[:100] + "..." if len(resp) > 100 else resp
                status_tag = "[green]SUCCESS ✅[/green]" if status == "success" else "[red]ERROR ❌[/red]"
                summary_table.add_row(name, status_tag, task[:26] + "..." if len(task) > 26 else task, preview)

            console.print(summary_table)
            console.print(
                f"   [dim]↳ Layer {layer_num} Total: [bold green]{success_count} succeeded[/bold green], "
                f"[bold red]{error_count} failed[/bold red][/dim]\n"
            )
        else:
            count = result_count if result_count is not None else 0
            console.print(
                f"📦 [bold green]Layer {layer_num} Complete[/bold green] "
                f"[dim]({count} Sub-Agent result(s) recorded)[/dim]\n"
            )

    @classmethod
    def log_all_layers_complete(cls, total_layers: int) -> None:
        """Visual divider rule when all layers are completed."""
        console.print()
        console.rule(
            f"[bold bright_green]🏁 ALL {total_layers} LAYER(S) EXECUTED SUCCESSFULLY[/bold bright_green]",
            style="bright_green",
        )
        console.print()

    # =========================================================================
    # 4. SUB-AGENT EXECUTION LOGS
    # =========================================================================

    @classmethod
    def log_subagent_start(
        cls,
        agent_name: str,
        agent_model: str,
        agent_task: str,
        tools: Optional[List[Any]] = None
    ) -> None:
        """Visual card for starting a sub-agent."""
        tools_names = []
        if tools:
            for t in tools:
                if isinstance(t, str):
                    tools_names.append(t)
                elif hasattr(t, "name"):
                    tools_names.append(t.name)
                elif isinstance(t, dict):
                    tools_names.append(t.get("tool_title", "tool"))
        tools_display = ", ".join(tools_names) if tools_names else "[dim]None[/dim]"

        body = (
            f"[bold cyan]Task:[/bold cyan] {agent_task}\n"
            f"[bold magenta]Model:[/bold magenta] {agent_model}\n"
            f"[bold blue]Available Tools:[/bold blue] {tools_display}"
        )
        console.print(
            Panel(
                body,
                title=f"[bold green]🤖 Executing Sub-Agent: [underline]{agent_name}[/underline][/bold green]",
                border_style="cyan",
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )

    @classmethod
    def log_subagent_completed(
        cls,
        agent_name: str,
        messages: List[Any],
        final_content: Any,
        task: Optional[str] = None
    ) -> None:
        """Visual card for completed sub-agent output and summary of tools used."""
        tool_calls_made = []
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", str(tc))
                    tool_args = tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {})
                    tool_calls_made.append((tool_name, tool_args))

        if tool_calls_made:
            table = Table(
                title=f"🔧 Tools Invoked by {agent_name} ({len(tool_calls_made)})",
                border_style="magenta",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta",
                expand=True
            )
            table.add_column("Tool", style="bold magenta", width=25)
            table.add_column("Arguments", style="dim")
            for t_name, t_args in tool_calls_made:
                table.add_row(t_name, json.dumps(t_args, ensure_ascii=False))
            console.print(table)

        content_str = str(final_content).strip()
        card_parts = []
        if task:
            card_parts.append(f"[bold cyan]Task:[/bold cyan] {task}")
        if tool_calls_made:
            card_parts.append(f"[bold magenta]Tools Used:[/bold magenta] {', '.join([t[0] for t in tool_calls_made])}")
        card_parts.append(f"\n[bold green]── Output ──────────────────────────────────────────────────────────[/bold green]\n{content_str if content_str else '[dim]No text generated[/dim]'}")

        console.print(
            Panel(
                "\n".join(card_parts),
                title=f"[bold green]✅ Agent Completed: {agent_name}[/bold green]",
                border_style="green",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        console.print()

    @classmethod
    def log_subagent_failed(
        cls,
        agent_name: str,
        error: Any,
        task: Optional[str] = None
    ) -> None:
        """Visual card for sub-agent execution failure."""
        body = ""
        if task:
            body += f"[bold white]Task:[/bold white] {task}\n\n"
        body += f"[bold red]Error Details:[/bold red]\n{error}"

        console.print(
            Panel(
                body,
                title=f"[bold red]❌ Agent Failed: {agent_name}[/bold red]",
                border_style="red",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )

    # =========================================================================
    # 5. DYNAMIC API TOOL EXECUTION LOGS (TOOL GENERATOR)
    # =========================================================================

    @classmethod
    def log_tool_executing(
        cls,
        tool_name: str,
        http_method: str,
        url: str,
        params: Any = None,
        body: Any = None,
        headers: Any = None
    ) -> None:
        """Visual card when a dynamic API tool is dispatched."""
        method_color = "bold green" if http_method.upper() == "GET" else "bold blue"
        req_lines = [
            f"[{method_color}]{http_method.upper()}[/{method_color}] [underline cyan]{url}[/underline cyan]"
        ]
        if params:
            req_lines.append(f"[bold yellow]Query Params:[/bold yellow] [dim]{json.dumps(params, ensure_ascii=False)}[/dim]")
        if body:
            req_lines.append(f"[bold magenta]Body/Payload:[/bold magenta] [dim]{json.dumps(body, ensure_ascii=False)}[/dim]")

        console.print(
            Panel(
                "\n".join(req_lines),
                title=f"[bold bright_magenta]🔧 Tool Dispatched: {tool_name}[/bold bright_magenta]",
                border_style="bright_magenta",
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )

    @classmethod
    def log_tool_executed(
        cls,
        tool_name: str,
        http_method: str,
        url: str,
        status_code: Optional[int],
        elapsed_ms: float,
        response_preview: str,
        is_error: bool = False
    ) -> None:
        """Visual card when an API tool completes execution."""
        status_style = "bold green" if (status_code and status_code < 400 and not is_error) else "bold red"
        status_label = f"[{status_style}]HTTP {status_code or 'ERR'}[/{status_style}]"
        latency_label = f"[dim cyan]{elapsed_ms:.1f}ms[/dim cyan]"

        preview = response_preview.strip()
        if len(preview) > 350:
            preview = preview[:350] + "\n... [dim](truncated preview)[/dim]"

        resp_content = (
            f"[bold white]Status:[/bold white] {status_label} | [bold white]Latency:[/bold white] {latency_label}\n"
            f"[dim]{preview}[/dim]"
        )
        border_style = "green" if not is_error else "red"

        console.print(
            Panel(
                resp_content,
                title=f"[bold {border_style}]⚡ Tool Result: {tool_name}[/bold {border_style}]",
                border_style=border_style,
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )

    # =========================================================================
    # 6. TOOL DISCOVERY WORKFLOW LOGS
    # =========================================================================

    @classmethod
    def log_tool_discovery_start(cls, task: str) -> None:
        """Visual banner for starting the tool discovery workflow."""
        console.print()
        console.rule(
            f"[bold magenta]🔍 TOOL DISCOVERY WORKFLOW: \"{task[:60]}\"[/bold magenta]",
            style="magenta",
        )
        console.print()

    @classmethod
    def log_tool_discovery_analysis(cls, task: str, queries: List[str]) -> None:
        """Visual card for task analysis and extracted search queries."""
        query_items = "\n".join([f"  [bold cyan]•[/bold cyan] [white]{q}[/white]" for q in queries]) if queries else "  [dim]None[/dim]"
        body = (
            f"[bold yellow]Analyzed Task:[/bold yellow] [white]{task}[/white]\n\n"
            f"[bold green]Generic Capability Queries ({len(queries)}):[/bold green]\n"
            f"{query_items}"
        )
        console.print(
            Panel(
                body,
                title="[bold magenta]🔍 [Node: analyze_task] Task Breakdown[/bold magenta]",
                border_style="magenta",
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )

    @classmethod
    def log_tool_discovery_db_search(cls, queries: List[str], tools_found: List[Dict[str, Any]]) -> None:
        """Visual table or card for vector database search results."""
        if tools_found:
            table = Table(
                title=f"🗄️ [Node: explore_db] Local Database Matches ({len(tools_found)} Found)",
                border_style="cyan",
                box=box.ROUNDED,
                header_style="bold cyan",
                show_header=True,
                expand=True
            )
            table.add_column("Tool Title", style="bold cyan", width=22)
            table.add_column("Method", justify="center", width=8)
            table.add_column("Description", style="white")

            for t in tools_found:
                title = t.get("tool_title", "tool")
                method = t.get("http_method", "GET")
                desc = t.get("description", "")
                table.add_row(title, method, desc[:70] + "..." if len(desc) > 70 else desc)

            console.print(table)
        else:
            console.print(
                Panel(
                    f"[dim yellow]Searched {len(queries)} query vector(s) in local database. No matching existing tools found.[/dim yellow]",
                    title="🗄️ [Node: explore_db] Local Database Search",
                    border_style="dim yellow",
                    box=box.ROUNDED,
                    padding=(0, 2),
                )
            )

    @classmethod
    def log_tool_discovery_evaluation(cls, is_sufficient: bool, missing_capabilities: List[str]) -> None:
        """Visual card for tool sufficiency evaluation."""
        if is_sufficient:
            status = "[bold green]SUFFICIENT ✅[/bold green] [dim]Existing tools satisfy all requirements.[/dim]"
        else:
            status = "[bold yellow]INSUFFICIENT ⚠️[/bold yellow] [dim]External tools must be discovered.[/dim]"

        missing_list = ""
        if missing_capabilities:
            items = "\n".join([f"  [bold red]•[/bold red] [white]{c}[/white]" for c in missing_capabilities])
            missing_list = f"\n\n[bold yellow]Missing Capabilities Needed ({len(missing_capabilities)}):[/bold yellow]\n{items}"

        console.print(
            Panel(
                f"[bold white]Status:[/bold white] {status}{missing_list}",
                title="⚖️ [Node: evaluate_tools] Sufficiency Evaluation",
                border_style="green" if is_sufficient else "yellow",
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )

    @classmethod
    def log_tool_discovery_web_extracted(cls, capability: str, tool_def: Dict[str, Any]) -> None:
        """Visual card for web-searched and LLM-extracted public API definition."""
        tool_title = tool_def.get("tool_title", "API Tool")
        method = tool_def.get("http_method", "GET").upper()
        url = tool_def.get("api_url", "")
        desc = tool_def.get("description", "")
        args = tool_def.get("argument", {})
        test_args = tool_def.get("test_arguments", {})

        body = (
            f"[bold magenta]Target Capability:[/bold magenta] [white]{capability}[/white]\n"
            f"[bold cyan]Tool Name:[/bold cyan] [bold white]{tool_title}[/bold white]\n"
            f"[bold green]Endpoint:[/bold green] [{ 'bold green' if method == 'GET' else 'bold blue' }]{method}[/] [underline]{url}[/underline]\n"
            f"[bold white]Description:[/bold white] [dim]{desc}[/dim]\n"
            f"[bold yellow]Arguments Schema:[/bold yellow] [dim]{json.dumps(args, ensure_ascii=False)}[/dim]\n"
            f"[bold blue]Sample Test Args:[/bold blue] [dim]{json.dumps(test_args, ensure_ascii=False)}[/dim]"
        )
        console.print(
            Panel(
                body,
                title=f"🌐 [Node: web_search] Extracted Free Public API: [underline]{tool_title}[/underline]",
                border_style="magenta",
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )

    @classmethod
    def log_tool_discovery_test(
        cls,
        tool_title: str,
        test_args: Dict[str, Any],
        passed: bool,
        result_preview: str
    ) -> None:
        """Visual card for testing the discovered web API tool."""
        status_tag = "[bold green]PASSED ✅[/bold green]" if passed else "[bold red]FAILED ❌[/bold red]"
        border = "green" if passed else "red"

        preview = result_preview.strip()
        if len(preview) > 250:
            preview = preview[:250] + "..."

        body = (
            f"[bold white]Test Status:[/bold white] {status_tag}\n"
            f"[bold cyan]Test Arguments:[/bold cyan] [dim]{json.dumps(test_args, ensure_ascii=False)}[/dim]\n"
            f"[bold white]Execution Output:[/bold white]\n[dim]{preview}[/dim]"
        )
        console.print(
            Panel(
                body,
                title=f"🧪 [Node: test_tool] Validation: [underline]{tool_title}[/underline]",
                border_style={True: "green", False: "red"}[passed],
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )

    @classmethod
    def log_tool_discovery_stored(cls, stored_count: int) -> None:
        """Visual notification for caching validated tools to DB."""
        if stored_count > 0:
            console.print(
                Panel(
                    f"[bold green]Successfully indexed and stored {stored_count} validated tool(s) into PostgreSQL Vector DB.[/bold green]",
                    title="💾 [Node: store_tool] Database Caching",
                    border_style="green",
                    box=box.ROUNDED,
                    padding=(0, 2),
                )
            )
        else:
            console.print(
                Panel(
                    "[dim]No new tools saved to DB.[/dim]",
                    title="💾 [Node: store_tool] Database Caching",
                    border_style="dim",
                    box=box.ROUNDED,
                    padding=(0, 2),
                )
            )

    @classmethod
    def log_tool_discovery_node(
        cls,
        node_name: str,
        description: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Visual node step in tool discovery (generic fallback)."""
        lines = [f"[bold cyan]{description}[/bold cyan]"]
        if details:
            for k, v in details.items():
                lines.append(f"  [bold yellow]{k}:[/bold yellow] [white]{v}[/white]")

        console.print(
            Panel(
                "\n".join(lines),
                title=f"[bold bright_magenta]Node: [{node_name}][/bold bright_magenta]",
                border_style="magenta",
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )

    @classmethod
    def log_tool_discovery_complete(cls, tools_found: List[Dict[str, Any]]) -> None:
        """Visual summary table of discovered tools."""
        console.print()
        if tools_found:
            table = Table(
                title=f"✅ Tool Discovery Complete ({len(tools_found)} Tools Ready)",
                border_style="bright_green",
                box=box.ROUNDED,
                header_style="bold bright_green",
                show_header=True,
                expand=True
            )
            table.add_column("Tool Title", style="bold cyan", width=24)
            table.add_column("Method", justify="center", width=8)
            table.add_column("Endpoint URL", style="white")
            table.add_column("Description", style="dim")

            for t in tools_found:
                title = t.get("tool_title", "tool")
                method = t.get("http_method", "GET")
                url = t.get("api_url", "")
                desc = t.get("description", "")
                table.add_row(title, method, url[:40] + "..." if len(url) > 40 else url, desc[:50] + "..." if len(desc) > 50 else desc)

            console.print(table)
        else:
            console.print("[yellow]⚠️  Tool Discovery Finished: No external tools needed or found.[/yellow]")
        console.print()

    # =========================================================================
    # 7. FINAL SYNTHESIS & WARNING LOGS
    # =========================================================================

    @classmethod
    def log_final_response(cls, final_response: str) -> None:
        """Visual highlight panel for the final workflow synthesized response."""
        console.print(
            Panel(
                str(final_response).strip(),
                title="[bold gold1]🌟 FINAL SYNTHESIZED WORKFLOW RESPONSE[/bold gold1]",
                border_style="gold1",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        console.print()

    @classmethod
    def log_warning(cls, message: str) -> None:
        """Visual warning alert."""
        console.print(f"[bold yellow]⚠️  WARNING:[/bold yellow] {message}")
