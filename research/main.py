from research.workflows.tool_descovery_workflow.tool_discovery import ToolDiscoveryWorkflow
from research.workflows.main_workflow.main_workflow import MainWorkFlow
from research.db_operations.main import ToolDBClient
from app.core.config import settings

class Research:
    openRouterAPIKey:str
    toolDiscoveryModel:str
    toolDiscoveryModelTemperature:float
    mainWorkflowModel:str
    mainWorkflowModelTemperature:float
    projectApiKey:str
    

    def __init__(self):
        pass

    def configure(self, openRouterAPIKey: str, toolDiscoveryModel: str, toolDiscoveryModelTemperature: float, projectApiKey: str = None, mainWorkflowModel: str = "deepseek/deepseek-v4-flash", mainWorkflowModelTemperature: float = 0.0):

        """
        Args:-
            openRouterAPIKey (str): The OpenRouter API key.
            toolDiscoveryModel (str): The model to use for tool discovery.
            toolDiscoveryModelTemperature (float): The temperature to use for tool discovery.
            mainWorkflowModel (str): The model to use for the main workflow.
            mainWorkflowModelTemperature (float): The temperature to use for the main workflow.
        """
        if not isinstance(openRouterAPIKey, str) or not openRouterAPIKey.strip():
            raise ValueError("openRouterAPIKey must be a valid, non-empty string.")
            
        if not isinstance(toolDiscoveryModel, str) or not toolDiscoveryModel.strip():
            raise ValueError("toolDiscoveryModel must be a valid, non-empty string.")
            
        if not isinstance(toolDiscoveryModelTemperature, (int, float)):
            raise TypeError("toolDiscoveryModelTemperature must be a numeric value.")
            
        if not (0.0 <= toolDiscoveryModelTemperature <= 2.0):       
            raise ValueError("toolDiscoveryModelTemperature must be between 0.0 and 2.0.")
            
        if not isinstance(mainWorkflowModel, str) or not mainWorkflowModel.strip():
            raise ValueError("mainWorkflowModel must be a valid, non-empty string.")
            
        if not isinstance(mainWorkflowModelTemperature, (int, float)):
            raise TypeError("mainWorkflowModelTemperature must be a numeric value.")
            
        if not (0.0 <= mainWorkflowModelTemperature <= 2.0):       
            raise ValueError("mainWorkflowModelTemperature must be between 0.0 and 2.0.")
            
        self.openRouterAPIKey = openRouterAPIKey.strip()
        self.toolDiscoveryModel = toolDiscoveryModel.strip()
        self.toolDiscoveryModelTemperature = float(toolDiscoveryModelTemperature)
        self.mainWorkflowModel = mainWorkflowModel.strip()
        self.mainWorkflowModelTemperature = float(mainWorkflowModelTemperature)
        self.projectApiKey = projectApiKey.strip() if projectApiKey else None

        # Initialize the DB Client
        api_key = self.projectApiKey or settings.DUMMY_API_KEY
        base_url = f"http://127.0.0.1:8000{settings.API_V1_STR}"
        db_client = ToolDBClient(base_url=base_url, api_key=api_key)

        self.tool_discovery_workflow = ToolDiscoveryWorkflow(
            openRouterAPIKey=self.openRouterAPIKey,
            toolDiscoveryModel=self.toolDiscoveryModel,
            toolDiscoveryModelTemperature=self.toolDiscoveryModelTemperature,
            db_client=db_client
        )
        
        self.main_workflow = MainWorkFlow(
            api_key=self.openRouterAPIKey,
            model_name=self.mainWorkflowModel,
            temperature=self.mainWorkflowModelTemperature
        )

    async def run(self, query: str):
        """ 
        Args:-
            query (str): The query to run the tool discovery agent with.
        """
       
        response = await self.tool_discovery_workflow.tool_discovery_workflow_run(query)
       
        return response

