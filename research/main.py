from research.agents.tool_descovery.tool_discovery import ToolDiscoveryWorkflow

class Research:
    openRouterAPIKey:str
    toolDiscoveryModel:str
    toolDiscoveryModelTemperature:float
    


    def __init__(self):
        pass

    def configure(self, openRouterAPIKey: str, toolDiscoveryModel: str, toolDiscoveryModelTemperature: float):

        """
        Args:-
            openRouterAPIKey (str): The OpenRouter API key.
            toolDiscoveryModel (str): The model to use for tool discovery.
            toolDiscoveryModelTemperature (float): The temperature to use for tool discovery.
        """
        if not isinstance(openRouterAPIKey, str) or not openRouterAPIKey.strip():
            raise ValueError("openRouterAPIKey must be a valid, non-empty string.")
            
        if not isinstance(toolDiscoveryModel, str) or not toolDiscoveryModel.strip():
            raise ValueError("toolDiscoveryModel must be a valid, non-empty string.")
            
        if not isinstance(toolDiscoveryModelTemperature, (int, float)):
            raise TypeError("toolDiscoveryModelTemperature must be a numeric value.")
            
        if not (0.0 <= toolDiscoveryModelTemperature <= 2.0):       
            raise ValueError("toolDiscoveryModelTemperature must be between 0.0 and 2.0.")
            
        self.openRouterAPIKey = openRouterAPIKey.strip()
        self.toolDiscoveryModel = toolDiscoveryModel.strip()
        self.toolDiscoveryModelTemperature = float(toolDiscoveryModelTemperature)


        """create the tool discovery agent"""
        self.tool_discovery_workflow = ToolDiscoveryWorkflow(
            openRouterAPIKey=self.openRouterAPIKey,
            toolDiscoveryModel=self.toolDiscoveryModel,
            toolDiscoveryModelTemperature=self.toolDiscoveryModelTemperature
        )

    async def run(self, query: str):
        """ 
        Args:-
            query (str): The query to run the tool discovery agent with.
        """
       

        response = await self.tool_discovery_workflow.run(query)
       
        return response
