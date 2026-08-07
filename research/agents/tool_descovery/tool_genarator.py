from langchain_core.tools import StructuredTool
from pydantic import create_model
import requests

def create_dynamic_api_tool(tool_dict: dict) -> StructuredTool:
    """
    Dynamically generates a runnable LangChain StructuredTool from a dictionary
    containing api_url, http_method, headers, and argument schema.
    """
    tool_title = tool_dict.get("tool_title", "dynamic_tool")
    description = tool_dict.get("description", "A dynamically generated tool.")
    api_url = tool_dict.get("api_url")
    http_method = tool_dict.get("http_method", "GET").upper()
    headers = tool_dict.get("headers") or {}
    argument_schema = tool_dict.get("argument") or {}
    
    # 1. Create the Pydantic schema dynamically for the LLM
    fields = {}
    for key, val in argument_schema.items():
        # Assuming simple string type for now for these dynamic inputs
        fields[key] = (str, ...)
        
    # LangChain requires a unique name for the Pydantic class
    DynamicArgsSchema = create_model(f"{tool_title}Schema", **fields)

    # 2. Define the execution function that will run when the LLM calls it
    def execute_api_call(**kwargs):
        print(f"\n[EXECUTE] Running dynamic tool '{tool_title}' targeting {api_url}")
        print(f"[EXECUTE] Method: {http_method}, Headers: {headers}, Payload: {kwargs}")
        
        # Prepare params or json based on method
        params = None
        json_data = None
        
        if http_method == "GET":
            params = kwargs
        else:
            json_data = kwargs
            
        try:
            # Execute the actual API call
            response = requests.request(
                method=http_method, 
                url=api_url, 
                headers=headers, 
                params=params, 
                json=json_data,
                timeout=10
            )
            response.raise_for_status() # Raise an exception for bad status codes
            return response.text
        except Exception as e:
            return f"Error executing tool: {e}"

    # 3. Build and return the structured tool
    return StructuredTool.from_function(
        func=execute_api_call,
        name=tool_title,
        description=description,
        args_schema=DynamicArgsSchema
    )
