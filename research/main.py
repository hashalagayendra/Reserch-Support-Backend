from research.agents.tool_discovery import ToolDiscoveryAgent

class Research:
    def __init__(self):
        # Initialize the agents you will use in this main class
        self.tool_discovery_agent = ToolDiscoveryAgent()

    def run(self, query: str):
        """Runs the tool discovery agent with the given query."""
        response = self.tool_discovery_agent.run(query)
        return response
