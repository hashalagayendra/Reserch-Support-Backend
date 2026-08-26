import re
import urllib.parse
from typing import Any, Dict, Tuple, Type
import requests
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, create_model


def _map_to_python_type(type_name: Any) -> Type:
    """Maps a schema type string (e.g. 'int', 'number', 'bool', 'string') to a Python type."""
    if isinstance(type_name, dict):
        type_str = str(type_name.get("type", "string")).lower()
    elif isinstance(type_name, str):
        type_str = type_name.lower()
    else:
        type_str = "string"

    if "str" in type_str or "text" in type_str or "string" in type_str:
        return str
    if "int" in type_str:
        return int
    if "number" in type_str or "float" in type_str or "double" in type_str:
        return float
    if "bool" in type_str or "boolean" in type_str:
        return bool
    if "list" in type_str or "array" in type_str:
        return list
    if "dict" in type_str or "object" in type_str:
        return dict
    return str


def _build_pydantic_schema(tool_title: str, argument_schema: Dict[str, Any]) -> Type[BaseModel]:
    """Generates a dynamic Pydantic schema model for LangChain tool arguments including descriptions."""
    fields = {}
    clean_title = re.sub(r'[^a-zA-Z0-9_]', '_', tool_title)

    for key, val in argument_schema.items():
        clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', key)
        python_type = _map_to_python_type(val)

        description = ""
        is_required = False
        default_val = None

        if isinstance(val, dict):
            description = val.get("description", "")
            is_required = val.get("required", False)
            default_val = val.get("default", ... if is_required else None)

        if is_required and default_val is None:
            field_def = Field(..., description=description)
        else:
            field_def = Field(default=default_val, description=description)

        fields[clean_key] = (python_type, field_def)

    return create_model(f"{clean_title}Schema", **fields)


def _categorize_parameters(
    kwargs: Dict[str, Any],
    argument_schema: Dict[str, Any],
    http_method: str,
    target_url: str
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Categorizes flat function arguments into:
    (path_params, query_params, body_params, header_params)
    based on the OpenAPI 'in' attribute or HTTP method heuristics.
    """
    path_params = {}
    query_params = {}
    body_params = {}
    header_params = {}

    placeholders = set(re.findall(r'\{([a-zA-Z0-9_]+)\}', target_url))

    for key, value in kwargs.items():
        if value is None:
            continue

        param_info = argument_schema.get(key, {})
        location = ""
        if isinstance(param_info, dict):
            location = str(param_info.get("in", "")).lower().strip()

        # If key is part of URL template placeholder, prioritize placeholder substitution
        if key in placeholders or f"{{{key}}}" in target_url:
            path_params[key] = value
        elif location == "path":
            path_params[key] = value
        elif location == "query":
            query_params[key] = value
        elif location == "body":
            if http_method == "GET":
                query_params[key] = value  # Fallback for GET requests
            else:
                body_params[key] = value
        elif location == "header":
            header_params[key] = value
        else:
            # Smart fallback when 'in' is omitted
            if http_method == "GET":
                query_params[key] = value
            else:
                body_params[key] = value

    return path_params, query_params, body_params, header_params


def _format_url_placeholders(url_template: str, path_params: Dict[str, Any], all_kwargs: Dict[str, Any]) -> str:
    """Substitutes URL path placeholders like {id} with URL-encoded values."""
    formatted_url = url_template
    placeholders = re.findall(r'\{([a-zA-Z0-9_]+)\}', formatted_url)

    for key in placeholders:
        val = path_params.get(key) if key in path_params else all_kwargs.get(key)
        if val is not None:
            encoded_val = urllib.parse.quote_plus(str(val))
            formatted_url = formatted_url.replace(f"{{{key}}}", encoded_val)
        else:
            raise ValueError(f"Missing required parameter '{key}' for URL placeholder in '{url_template}'")

    return formatted_url


def _send_http_request(
    http_method: str,
    url: str,
    base_headers: Dict[str, Any],
    query_params: Dict[str, Any],
    body_params: Dict[str, Any],
    header_params: Dict[str, Any]
) -> str:
    """Executes the HTTP request with properly routed query, body, and header parameters."""
    req_headers = dict(base_headers)
    req_headers.update({k: str(v) for k, v in header_params.items()})

    params = query_params if query_params else None
    json_data = None
    form_data = None

    if http_method in ["POST", "PUT", "PATCH", "DELETE"]:
        content_type = req_headers.get("Content-Type", req_headers.get("content-type", ""))
        if "application/x-www-form-urlencoded" in content_type:
            form_data = body_params if body_params else None
        else:
            if not content_type:
                req_headers["Content-Type"] = "application/json"
            json_data = body_params if body_params else None

    print(f"\n[EXECUTE] Dynamic Tool Request -> {http_method} {url}")
    print(f"[EXECUTE] Query: {params} | Body: {json_data or form_data} | Headers: {req_headers}")

    try:
        response = requests.request(
            method=http_method,
            url=url,
            headers=req_headers,
            params=params,
            json=json_data,
            data=form_data,
            timeout=10
        )
        response.raise_for_status()
        return response.text
    except requests.exceptions.HTTPError as http_err:
        err_details = response.text if response is not None else ""
        return f"Error executing tool ({http_err}): {err_details}"
    except Exception as e:
        return f"Error executing tool: {e}"


def create_dynamic_api_tool(tool_dict: Dict[str, Any]) -> StructuredTool:
    """
    Dynamically generates a runnable LangChain StructuredTool from a dictionary
    containing api_url, http_method, headers, and argument schema.
    """
    raw_title = tool_dict.get("tool_title", "dynamic_tool")
    tool_title = re.sub(r'[^a-zA-Z0-9_-]', '_', raw_title)
    description = tool_dict.get("description", "A dynamically generated tool.")
    api_url = tool_dict.get("api_url", "")
    http_method = tool_dict.get("http_method", "GET").upper()
    headers = dict(tool_dict.get("headers") or {})
    argument_schema = tool_dict.get("argument") or {}

    # 1. Build schema for LLM
    args_schema = _build_pydantic_schema(tool_title, argument_schema)

    # 2. Execution function
    def execute_api_call(**kwargs):
        path_params, query_params, body_params, header_params = _categorize_parameters(
            kwargs=kwargs,
            argument_schema=argument_schema,
            http_method=http_method,
            target_url=api_url
        )
        try:
            final_url = _format_url_placeholders(api_url, path_params, kwargs)
        except ValueError as val_err:
            return f"Error executing tool: {val_err}"

        return _send_http_request(
            http_method=http_method,
            url=final_url,
            base_headers=headers,
            query_params=query_params,
            body_params=body_params,
            header_params=header_params
        )

    # 3. Create and return StructuredTool
    return StructuredTool.from_function(
        func=execute_api_call,
        name=tool_title,
        description=description,
        args_schema=args_schema
    )
