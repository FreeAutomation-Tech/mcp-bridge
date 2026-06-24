import json


JSON_RPC_VERSION = "2.0"
MCP_PROTOCOL_VERSION = "2024-11-05"


def build_request(method, params=None, request_id=1):
    msg = {
        "jsonrpc": JSON_RPC_VERSION,
        "id": request_id,
        "method": method,
    }
    if params is not None:
        msg["params"] = params
    return msg


def build_notification(method, params=None):
    msg = {
        "jsonrpc": JSON_RPC_VERSION,
        "method": method,
    }
    if params is not None:
        msg["params"] = params
    return msg


def build_success(result, request_id):
    return {
        "jsonrpc": JSON_RPC_VERSION,
        "id": request_id,
        "result": result,
    }


def build_error(code, message, request_id, data=None):
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {
        "jsonrpc": JSON_RPC_VERSION,
        "id": request_id,
        "error": err,
    }


def parse_message(line):
    return json.loads(line)


def serialize(msg):
    return json.dumps(msg, ensure_ascii=False)


def make_initialization():
    return build_request(
        "initialize",
        {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {
                "name": "mcp-bridge",
                "version": "0.1.0",
            },
        },
        request_id=1,
    )


def make_initialized_notification():
    return build_notification("notifications/initialized")


def make_list_tools_request(request_id):
    return build_request("tools/list", request_id=request_id)


def make_call_tool_request(name, arguments, request_id):
    return build_request(
        "tools/call",
        {"name": name, "arguments": arguments},
        request_id=request_id,
    )


def convert_mcp_tool_to_claude(mcp_tool):
    return {
        "name": mcp_tool["name"],
        "description": mcp_tool.get("description", ""),
        "input_schema": mcp_tool.get("inputSchema", {"type": "object"}),
    }
