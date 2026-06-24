import json
import os
import urllib.request
import urllib.error


ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_MAX_TOKENS = 4096
MAX_ITERATIONS = 15

SYSTEM_PROMPT = (
    "You are an AI assistant with access to tools provided by an MCP "
    "(Model Context Protocol) server. Your task is to help the user "
    "by using the available tools to accomplish their request. "
    "Think step by step about which tools to call and in what order. "
    "You can call multiple tools in sequence. "
    "When you have enough information, provide a clear and concise answer."
)


class ClaudeAPIError(Exception):
    pass


class ClaudeClient:

    def __init__(self, api_key=None, model=DEFAULT_MODEL,
                 max_tokens=DEFAULT_MAX_TOKENS):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY "
                "env var or pass --api-key"
            )
        self.model = model
        self.max_tokens = max_tokens

    def _request(self, payload):
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            ANTHROPIC_API_URL,
            data=data,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )
        try:
            resp = urllib.request.urlopen(req)
            body = resp.read().decode("utf-8")
            return json.loads(body)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise ClaudeAPIError(
                f"Anthropic API error {e.code}: {body}"
            ) from e
        except urllib.error.URLError as e:
            raise ClaudeAPIError(f"Request failed: {e.reason}") from e

    def send_with_tools(self, messages, tools):
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": SYSTEM_PROMPT,
            "messages": messages,
            "tools": tools,
        }
        return self._request(payload)
