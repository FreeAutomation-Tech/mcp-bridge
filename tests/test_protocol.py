from mcp_bridge.protocol import (
    build_request,
    build_notification,
    build_success,
    build_error,
    make_initialization,
    make_initialized_notification,
    make_list_tools_request,
    make_call_tool_request,
    convert_mcp_tool_to_claude,
    serialize,
    parse_message,
)


class TestBuildRequest:

    def test_basic_request(self):
        msg = build_request("tools/list", request_id=1)
        assert msg["jsonrpc"] == "2.0"
        assert msg["id"] == 1
        assert msg["method"] == "tools/list"
        assert "params" not in msg

    def test_request_with_params(self):
        msg = build_request("tools/call",
                            {"name": "test"}, request_id=2)
        assert msg["params"] == {"name": "test"}


class TestBuildNotification:

    def test_notification(self):
        msg = build_notification("notifications/initialized")
        assert msg["jsonrpc"] == "2.0"
        assert "id" not in msg
        assert msg["method"] == "notifications/initialized"


class TestBuildSuccess:

    def test_success(self):
        msg = build_success({"tools": []}, request_id=1)
        assert msg["result"] == {"tools": []}
        assert msg["id"] == 1


class TestBuildError:

    def test_error(self):
        msg = build_error(-32700, "Parse error", request_id=1)
        assert msg["error"]["code"] == -32700


class TestMakeInitialization:

    def test_structure(self):
        msg = make_initialization()
        assert msg["method"] == "initialize"
        assert msg["params"]["protocolVersion"] == "2024-11-05"
        assert msg["params"]["clientInfo"]["name"] == "mcp-bridge"


class TestMakeInitializedNotification:

    def test_structure(self):
        msg = make_initialized_notification()
        assert msg["method"] == "notifications/initialized"


class TestMakeListToolsRequest:

    def test_structure(self):
        msg = make_list_tools_request(request_id=5)
        assert msg["method"] == "tools/list"
        assert msg["id"] == 5


class TestMakeCallToolRequest:

    def test_structure(self):
        msg = make_call_tool_request(
            "read_file", {"path": "/tmp"}, request_id=3
        )
        assert msg["method"] == "tools/call"
        assert msg["params"]["name"] == "read_file"
        assert msg["params"]["arguments"] == {"path": "/tmp"}


class TestConvertMcpToolToClaude:

    def test_conversion(self):
        mcp_tool = {
            "name": "read_file",
            "description": "Read a file",
            "inputSchema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        }
        result = convert_mcp_tool_to_claude(mcp_tool)
        assert result["name"] == "read_file"
        assert result["description"] == "Read a file"
        assert result["input_schema"]["type"] == "object"

    def test_minimal_tool(self):
        mcp_tool = {"name": "ping"}
        result = convert_mcp_tool_to_claude(mcp_tool)
        assert result["name"] == "ping"
        assert result["input_schema"]["type"] == "object"


class TestSerializeParse:

    def test_roundtrip(self):
        msg = build_request("test", request_id=1)
        line = serialize(msg)
        parsed = parse_message(line)
        assert parsed == msg
