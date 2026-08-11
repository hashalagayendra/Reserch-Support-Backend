import requests
import time
from typing import Dict, Any, Optional


def get_recent_models(api_key: Optional[str] = None) -> list:
    """
    Fetches the list of all available models from the OpenRouter API created in the last 6 months.
    """
    url = "https://openrouter.ai/api/v1/models"
    headers = {}
    
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        models = data.get("data", [])
        
        # Calculate timestamp for 6 months ago (approx 180 days)
        six_months_ago = time.time() - (180 * 24 * 60 * 60)
        
        keys_to_extract = [
            "id", "canonical_slug", "name", "description", 
            "architecture", "per_request_limits", "links", "reasoning"
        ]
        
        recent_models = []
        for model in models:
            created_at = model.get("created", 0)
            if created_at >= six_months_ago:
                filtered_model = {k: model.get(k) for k in keys_to_extract if k in model}
                recent_models.append(filtered_model)
                
        return recent_models
    except requests.exceptions.RequestException as e:
        print(f"Error fetching models from OpenRouter: {e}")
        return []

def get_each_model_details(model_id: str, api_key: Optional[str] = None) -> list:
    """
    Fetches the endpoints/routing data (and thus providers) for a specific model from OpenRouter.
    """
    url = f"https://openrouter.ai/api/v1/models/{model_id}/endpoints"
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json().get("data", {})
        return data.get("endpoints", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching endpoints for {model_id}: {e}")
        return []

def get_design_arena_benchmarks(api_key: Optional[str] = None) -> list:
    """
    Fetches the benchmarks from OpenRouter API, filtered for the Design Arena source.
    """
    url = "https://openrouter.ai/api/v1/benchmarks"
    params = {"source": "design-arena"}
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json().get("data", [])
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching benchmarks from OpenRouter: {e}")
        return []

