from mcp_bridge.protocol import convert_mcp_tool_to_claude
from mcp_bridge.transport import McpStdioTransport
from mcp_bridge.llm import ClaudeClient, MAX_ITERATIONS

TOOL_CALL_ERR = "Error calling tool '{name}': {error}"


class BridgeError(Exception):
    pass


def _extract_tools(transport):
    req_id = transport.send_request("tools/list")
    resp = transport.read_response(req_id)
    if "error" in resp:
        err = resp["error"]
        raise BridgeError(
            f"Failed to list tools: {err.get('message', str(err))}"
        )
    return resp.get("result", {}).get("tools", [])


def _call_mcp_tool(transport, name, arguments):
    req_id = transport.send_request(
        "tools/call",
        {"name": name, "arguments": arguments},
    )
    resp = transport.read_response(req_id)
    if "error" in resp:
        err = resp["error"]
        return {
            "isError": True,
            "content": [
                {
                    "type": "text",
                    "text": TOOL_CALL_ERR.format(
                        name=name, error=err.get("message", str(err))
                    ),
                }
            ],
        }
    return resp.get("result", {})


def _format_tool_result(tool_name, result):
    content = result.get("content", [])
    text_parts = []
    for item in content:
        if item.get("type") == "text":
            text_parts.append(item.get("text", ""))
    text = "\n".join(text_parts)
    if not text:
        text = str(result)
    if len(text) > 50000:
        text = text[:50000] + "\n...[truncated]"
    return text


def run_bridge(server_command, query, api_key=None,
               model=None, max_tokens=None):
    transport = McpStdioTransport(server_command)

    try:
        if not transport.alive:
            stderr = transport.process.stderr.read()
            raise BridgeError(
                f"MCP server failed to start: {stderr}"
            )

        req_id = transport.send_request("initialize")
        resp = transport.read_response(req_id)
        if "error" in resp:
            err = resp["error"]
            raise BridgeError(
                "MCP initialization failed: "
                f"{err.get('message', str(err))}"
            )

        transport.send_notification("notifications/initialized")

        mcp_tools = _extract_tools(transport)
        claude_tools = [
            convert_mcp_tool_to_claude(t) for t in mcp_tools
        ]

        claude = ClaudeClient(
            api_key=api_key,
            model=model or ClaudeClient.DEFAULT_MODEL,
            max_tokens=max_tokens or ClaudeClient.DEFAULT_MAX_TOKENS,
        )

        messages = [{"role": "user", "content": query}]
        iteration = 0
        text_output = ""

        while iteration < MAX_ITERATIONS:
            iteration += 1
            response = claude.send_with_tools(messages, claude_tools)

            content_blocks = response.get("content", [])

            text_output = ""
            tool_uses = []

            for block in content_blocks:
                if block["type"] == "text":
                    text_output += block.get("text", "")
                elif block["type"] == "tool_use":
                    tool_uses.append(block)

            assistant_msg = {"role": "assistant", "content": content_blocks}
            messages.append(assistant_msg)

            if not tool_uses:
                return text_output

            for tool_use in tool_uses:
                result = _call_mcp_tool(
                    transport,
                    tool_use["name"],
                    tool_use.get("input", {}),
                )
                tool_text = _format_tool_result(
                    tool_use["name"], result
                )
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use["id"],
                            "content": tool_text,
                        }
                    ],
                })

        return (
            "Reached maximum iterations. "
            "Last response:\n" + text_output
        )

    finally:
        transport.close()
