import operator
from typing import TypedDict, Annotated, List, Dict, Any

from langchain_openrouter import ChatOpenRouter
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

from app.core.config import settings
from app.db.session import SessionLocal
from app.db.models import AITool

# --- STRUCTURED OUTPUT MODELS ---
class TaskAnalysis(BaseModel):
    search_queries: List[str] = Field(
        description="A list of specific search queries to find the tools needed to complete the task."
    )

class ToolEvaluation(BaseModel):
    is_sufficient: bool = Field(
        description="True if the provided tools are completely sufficient to accomplish the task, False otherwise."
    )
    missing_capabilities: List[str] = Field(
        description="A list of specific tool capabilities that are still missing to accomplish the task. Empty if is_sufficient is True."
    )

# --- STATE DEFINITION ---
class ToolDiscoveryState(TypedDict):
    task: str
    search_queries: List[str]
    local_tools_found: List[Dict]
    is_sufficient: bool
    missing_capabilities: List[str]
    web_tools_found: List[Dict]
    tested_tools: List[Dict]
    final_answer: str

# --- WORKFLOW CLASS ---
class ToolDiscoveryWorkflow:
    def __init__(
        self, 
        openRouterAPIKey: str = None, 
        toolDiscoveryModel: str = None, 
        toolDiscoveryModelTemperature: float = None,
        embeddingModel: str = None
    ):
        # Configuration
        api_key = openRouterAPIKey or settings.OPENROUTER_API_KEY
        model = toolDiscoveryModel or settings.TOOL_DISCOVERY_MODEL
        temp = toolDiscoveryModelTemperature if toolDiscoveryModelTemperature is not None else settings.TOOL_DISCOVERY_TEMPERATURE
        emb_model = embeddingModel or settings.EMBEDDING_MODEL
        
        # Initialize the LLM
        self.llm = ChatOpenRouter(
            model=model,
            temperature=temp,
            api_key=api_key
        )
        
        # Initialize Embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=api_key,
            model=emb_model
        )

        # Generate the custom graph
        self.workflow = self.generate_tool_discovery_workflow()

    def generate_tool_discovery_workflow(self):
        """Builds the advanced Tool Discovery Graph."""
        workflow = StateGraph(ToolDiscoveryState)
        
        # Add Nodes
        workflow.add_node("analyze_task", self.node_analyze_task)
        workflow.add_node("explore_db", self.node_explore_db)
        workflow.add_node("evaluate_tools", self.node_evaluate_tools)
        workflow.add_node("web_search", self.node_web_search)
        workflow.add_node("test_tool", self.node_test_tool)
        workflow.add_node("store_tool", self.node_store_tool)
        workflow.add_node("final_answer", self.node_final_answer)

        # Connect Nodes (Edges)
        workflow.add_edge(START, "analyze_task")
        workflow.add_edge("analyze_task", "explore_db")
        workflow.add_edge("explore_db", "evaluate_tools")
        
        # Conditional Edge after Evaluation
        workflow.add_conditional_edges(
            "evaluate_tools",
            self.route_after_evaluate,
            {
                "final_answer": "final_answer",
                "web_search": "web_search"
            }
        )
        
        workflow.add_edge("web_search", "test_tool")
        workflow.add_edge("test_tool", "store_tool")
        workflow.add_edge("store_tool", "final_answer")
        workflow.add_edge("final_answer", END)
        
        return workflow.compile()

    # --- ROUTING LOGIC ---
    def route_after_evaluate(self, state: ToolDiscoveryState) -> str:
        """If local tools are sufficient, go to final answer. Else, search the web."""
        if state.get("is_sufficient"):
            return "final_answer"
        return "web_search"

    # --- NODES ---
    def node_analyze_task(self, state: ToolDiscoveryState):
        """Uses LLM to break down the complex task into specific search queries."""
        task = state.get("task", "")
        print(f"--- [Node: analyze_task] Breaking down task: '{task}' ---")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an AI architect. Break down the user's task and determine what distinct AI tools or capabilities are required to accomplish it. Output a list of specific search queries to find these tools."),
            ("user", "Task: {task}")
        ])
        
        chain = prompt | self.llm.with_structured_output(TaskAnalysis)
        try:
            result = chain.invoke({"task": task})
            queries = result.search_queries
        except Exception as e:
            # Fallback if structured output fails
            print(f"    Failed to parse structured output: {e}. Using raw task as query.")
            queries = [task]
            
        print(f"    Generated Queries: {queries}")
        return {"search_queries": queries}

    def node_explore_db(self, state: ToolDiscoveryState):
        """Searches the local PostgreSQL vector database for each query."""
        queries = state.get("search_queries", [])
        print(f"--- [Node: explore_db] Searching DB for queries ---")
        
        db = SessionLocal()
        found_tools = []
        seen_titles = set()
        
        try:
            for query in queries:
                query_vector = self.embeddings.embed_query(query)
                # Get top 2 closest matches per query
                tools = db.query(AITool).order_by(AITool.vector_data.cosine_distance(query_vector)).limit(2).all()
                
                if tools:
                    for t in tools:
                        if t.tool_title not in seen_titles:
                            seen_titles.add(t.tool_title)
                            found_tools.append({
                                "tool_title": t.tool_title,
                                "description": t.description,
                                "argument": t.argument
                            })
                            print(f"    Found local tool: {t.tool_title}")
        finally:
            db.close()
            
        return {"local_tools_found": found_tools}

    def node_evaluate_tools(self, state: ToolDiscoveryState):
        """Uses LLM to evaluate if the found local tools are sufficient to complete the task."""
        task = state.get("task", "")
        local_tools = state.get("local_tools_found", [])
        print(f"--- [Node: evaluate_tools] Evaluating {len(local_tools)} found tools against the task ---")
        
        tools_desc = "\n".join([f"- {t['tool_title']}: {t['description']}" for t in local_tools]) if local_tools else "No local tools found."
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a tool evaluator. You will be given a task and a list of available tools. Determine if the provided tools are completely sufficient to accomplish the task. If not, list the specific missing capabilities."),
            ("user", "Task: {task}\n\nAvailable Tools:\n{tools}")
        ])
        
        chain = prompt | self.llm.with_structured_output(ToolEvaluation)
        try:
            result = chain.invoke({"task": task, "tools": tools_desc})
            is_sufficient = result.is_sufficient
            missing = result.missing_capabilities
        except Exception as e:
            # Fallback
            print(f"    Failed to parse structured output: {e}.")
            is_sufficient = False
            missing = ["Unknown missing capabilities"]
            
        print(f"    Is Sufficient? {is_sufficient}")
        if not is_sufficient:
            print(f"    Missing Capabilities: {missing}")
            
        return {"is_sufficient": is_sufficient, "missing_capabilities": missing}

    def node_web_search(self, state: ToolDiscoveryState):
        """Simulates searching the web for specifically missing capabilities."""
        missing = state.get("missing_capabilities", [])
        print(f"--- [Node: web_search] Searching Web for missing capabilities ---")
        
        mock_web_tools = []
        for capability in missing:
            print(f"    Mock searching for: {capability}")
            # MOCK WEB SEARCH: Returning a full tool payload representing a parsed API
            mock_web_tools.append({
                "tool_title": f"WebTool_{capability.replace(' ', '_').lower()}",
                "description": f"An excellent tool found on the web that provides: {capability}",
                "argument": {"search_query": {"type": "string", "description": "The thing to search"}},
                "api_url": f"https://mock-api.com/v1/{capability.replace(' ', '')}",
                "http_method": "GET",
                "headers": {"Authorization": "Bearer MOCK_TOKEN"}
            })
            
        return {"web_tools_found": mock_web_tools}

    def node_test_tool(self, state: ToolDiscoveryState):
        """Simulates testing the newly discovered web tools by creating a runnable tool and executing it."""
        from research.agents.tool_descovery.tool_genarator import create_dynamic_api_tool
        
        web_tools = state.get("web_tools_found", [])
        print("--- [Node: test_tool] Testing discovered web tools ---")
        
        tested = []
        for wt in web_tools:
            try:
                # 1. Create the actual runnable tool!
                runnable_tool = create_dynamic_api_tool(wt)
                print(f"    Created runnable tool: {runnable_tool.name}")
                
                # 2. Test the runnable tool with mock input
                test_result = runnable_tool.invoke({"search_query": "test run"})
                print(f"    Test Result: {test_result}")
                
                wt["tested_and_passed"] = True
            except Exception as e:
                print(f"    Failed to test tool {wt['tool_title']}: {e}")
                wt["tested_and_passed"] = False
                
            tested.append(wt)
            
        return {"tested_tools": tested}

    def node_store_tool(self, state: ToolDiscoveryState):
        """Stores the successfully tested tools into the local database."""
        tested_tools = state.get("tested_tools", [])
        print("--- [Node: store_tool] Caching validated tools to database ---")
        
        db = SessionLocal()
        try:
            for tt in tested_tools:
                if tt.get("tested_and_passed"):
                    vector = self.embeddings.embed_query(tt["description"])
                    # Using hardcoded project_id=1 as a dummy for now
                    new_tool = AITool(
                        project_id=1,
                        tool_title=tt["tool_title"],
                        description=tt["description"],
                        argument=tt["argument"],
                        vector_data=vector
                    )
                    db.add(new_tool)
            db.commit()
            print(f"    Successfully saved {len(tested_tools)} tools to DB.")
        except Exception as e:
            print(f"    Error storing tool: {e}")
            db.rollback()
        finally:
            db.close()
            
        return {}

    def node_final_answer(self, state: ToolDiscoveryState):
        """Generates the final response based on what was found."""
        local = state.get("local_tools_found", [])
        new_tools = state.get("tested_tools", [])
        is_sufficient = state.get("is_sufficient")
        
        msg = f"Task Analysis Complete. Local Tools Sufficient: {is_sufficient}\n\n"
        
        if local:
            msg += "(From Local Database)\n"
            for t in local:
                msg += f"- {t['tool_title']}: {t['description']}\n"
        
        if new_tools:
            msg += "\n(Newly Discovered & Tested from Web)\n"
            for t in new_tools:
                msg += f"- {t['tool_title']}: {t['description']}\n"
                
        print("--- [Node: final_answer] Complete ---")
        return {"final_answer": msg}

    async def tool_discovery_workflow_run(self, task: str):
        """Helper method to run the workflow with a complex task."""
        initial_state = {
            "task": task, 
            "search_queries": [],
            "local_tools_found": [], 
            "is_sufficient": False,
            "missing_capabilities": [],
            "web_tools_found": [],
            "tested_tools": [],
            "final_answer": ""
        }
        # Run the custom graph
        response = await self.workflow.ainvoke(initial_state)
        return response
