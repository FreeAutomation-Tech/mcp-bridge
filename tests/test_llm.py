import json
import os
import urllib.error

import pytest

from mcp_bridge.llm import ClaudeClient, ClaudeAPIError, SYSTEM_PROMPT


class FakeResponse:

    def __init__(self, data, code=200):
        self.data = json.dumps(data).encode("utf-8")
        self.code = code

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class TestClaudeClient:

    def test_init_without_key(self):
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]
        with pytest.raises(ValueError, match="API key"):
            ClaudeClient(api_key="")

    def test_init_with_key(self):
        client = ClaudeClient(api_key="sk-test")
        assert client.api_key == "sk-test"

    def test_init_with_env_var(self, mocker):
        mocker.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-env"})
        client = ClaudeClient()
        assert client.api_key == "sk-env"

    def test_api_error_handling(self, mocker):
        client = ClaudeClient(api_key="sk-test")

        mocker.patch(
            "mcp_bridge.llm.urllib.request.urlopen",
            side_effect=urllib.error.URLError("Connection refused"),
        )

        with pytest.raises(ClaudeAPIError, match="Connection refused"):
            client.send_with_tools(
                [{"role": "user", "content": "hi"}], []
            )

    def test_send_with_tools(self, mocker):
        client = ClaudeClient(api_key="sk-test")
        response_data = {
            "content": [
                {"type": "text", "text": "Hello!"}
            ],
            "stop_reason": "end_turn",
        }

        def fake_urlopen(*args, **kwargs):
            return FakeResponse(response_data)

        mocker.patch(
            "mcp_bridge.llm.urllib.request.urlopen",
            side_effect=fake_urlopen,
        )

        result = client.send_with_tools(
            [{"role": "user", "content": "hi"}],
            [{"name": "test_tool", "description": "", "input_schema": {}}],
        )
        assert result["content"][0]["text"] == "Hello!"

    def test_tool_use_response(self, mocker):
        client = ClaudeClient(api_key="sk-test")
        response_data = {
            "content": [
                {"type": "text", "text": "Using tool..."},
                {
                    "type": "tool_use",
                    "id": "toolu_abc123",
                    "name": "read_file",
                    "input": {"path": "/tmp/test.txt"},
                },
            ],
            "stop_reason": "tool_use",
        }

        def fake_urlopen(*args, **kwargs):
            return FakeResponse(response_data)

        mocker.patch(
            "mcp_bridge.llm.urllib.request.urlopen",
            side_effect=fake_urlopen,
        )

        result = client.send_with_tools(
            [{"role": "user", "content": "read file"}],
            [{"name": "read_file", "description": "", "input_schema": {}}],
        )
        blocks = result["content"]
        assert len(blocks) == 2
        assert blocks[1]["type"] == "tool_use"
        assert blocks[1]["name"] == "read_file"

    def test_system_prompt_available(self):
        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT) > 50
