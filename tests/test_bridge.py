import pytest

from mcp_bridge.bridge import run_bridge, BridgeError


class FakeTransport:

    def __init__(self):
        self.requests = []
        self.responses = []
        self.closed = False
        self._alive = True

    def send_request(self, method, params=None):
        self.requests.append((method, params))
        return len(self.requests)

    def send_notification(self, method, params=None):
        pass

    def read_response(self, expected_id):
        for resp in self.responses:
            if resp.get("id") == expected_id:
                return resp
        return {"id": expected_id, "result": {}}

    def close(self):
        self.closed = True

    @property
    def alive(self):
        return self._alive

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def fake_claude_response(content_blocks):
    return {
        "content": content_blocks,
        "stop_reason": "end_turn",
    }


class TestRunBridge:

    def test_simple_text_response(self, mocker):
        mocker.patch(
            "mcp_bridge.bridge.McpStdioTransport",
            return_value=FakeTransport(),
        )

        mocker.patch(
            "mcp_bridge.bridge.ClaudeClient",
        )
        mock_instance = mocker.patch(
            "mcp_bridge.bridge.ClaudeClient",
        ).return_value
        mock_instance.send_with_tools.return_value = fake_claude_response([
            {"type": "text", "text": "Hello from bridge!"},
        ])

        result = run_bridge(
            server_command="python -c \"\"",
            query="say hello",
            api_key="sk-test",
        )
        assert result == "Hello from bridge!"

    def test_tool_use_loop(self, mocker):
        transport = FakeTransport()
        transport.responses = [
            {"id": 1, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "test", "version": "1"},
            }},
            {"id": 2, "result": {
                "tools": [
                    {
                        "name": "echo",
                        "description": "Echo input",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"}
                            },
                            "required": ["text"],
                        },
                    }
                ]
            }},
            {"id": 3, "result": {
                "content": [
                    {"type": "text", "text": "echoed: hello"}
                ]
            }},
        ]

        mocker.patch(
            "mcp_bridge.bridge.McpStdioTransport",
            return_value=transport,
        )

        call_count = [0]

        def fake_send(messages, tools):
            call_count[0] += 1
            if call_count[0] == 1:
                return fake_claude_response([
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "echo",
                        "input": {"text": "hello"},
                    }
                ])
            return fake_claude_response([
                {"type": "text", "text": "Done: echoed hello"}
            ])

        mocker.patch(
            "mcp_bridge.bridge.ClaudeClient",
        )
        mock_instance = mocker.patch(
            "mcp_bridge.bridge.ClaudeClient",
        ).return_value
        mock_instance.send_with_tools.side_effect = fake_send

        result = run_bridge(
            server_command="python -c \"\"",
            query="echo hello",
            api_key="sk-test",
        )
        assert result == "Done: echoed hello"
        assert transport.closed is True

    def test_bridge_transport_failure(self, mocker):
        dead_transport = mocker.Mock()
        dead_transport.alive = False
        dead_transport.process.stderr.read.return_value = "error msg"

        mocker.patch(
            "mcp_bridge.bridge.McpStdioTransport",
            return_value=dead_transport,
        )

        with pytest.raises(BridgeError, match="failed to start"):
            run_bridge(
                server_command="bad_command",
                query="test",
                api_key="sk-test",
            )

    def test_max_iterations(self, mocker):
        transport = FakeTransport()

        mocker.patch(
            "mcp_bridge.bridge.McpStdioTransport",
            return_value=transport,
        )

        call_count = [0]

        def fake_send(messages, tools):
            call_count[0] += 1
            return fake_claude_response([
                {
                    "type": "tool_use",
                    "id": f"toolu_{call_count[0]}",
                    "name": "ping",
                    "input": {},
                }
            ])

        mocker.patch(
            "mcp_bridge.bridge.ClaudeClient",
        )
        mock_instance = mocker.patch(
            "mcp_bridge.bridge.ClaudeClient",
        ).return_value
        mock_instance.send_with_tools.side_effect = fake_send

        result = run_bridge(
            server_command="python -c \"\"",
            query="ping forever",
            api_key="sk-test",
        )
        assert "Reached maximum iterations" in result

    def test_mcp_tool_error(self, mocker):
        transport = FakeTransport()
        transport.responses = [
            {"id": 1, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "test", "version": "1"},
            }},
            {"id": 2, "result": {
                "tools": [
                    {
                        "name": "fail_tool",
                        "description": "Always fails",
                        "inputSchema": {"type": "object"},
                    }
                ]
            }},
            {"id": 3, "error": {
                "code": -32603,
                "message": "Internal error",
            }},
        ]

        mocker.patch(
            "mcp_bridge.bridge.McpStdioTransport",
            return_value=transport,
        )

        call_count = [0]

        def fake_send(messages, tools):
            call_count[0] += 1
            if call_count[0] == 1:
                return fake_claude_response([
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "fail_tool",
                        "input": {},
                    }
                ])
            return fake_claude_response([
                {"type": "text", "text": "Tool failed: Error calling tool"}
            ])

        mocker.patch(
            "mcp_bridge.bridge.ClaudeClient",
        )
        mock_instance = mocker.patch(
            "mcp_bridge.bridge.ClaudeClient",
        ).return_value
        mock_instance.send_with_tools.side_effect = fake_send

        result = run_bridge(
            server_command="python -c \"\"",
            query="run failing tool",
            api_key="sk-test",
        )
        assert "Error calling tool" in result
