# mcp-bridge

Bridge Claude to any MCP (Model Context Protocol) server via stdio. Run natural language queries against MCP tools.

## Installation

```bash
pip install mcp-bridge
```

Requires Python 3.9+ and an [Anthropic API key](https://console.anthropic.com/).

## Usage

```bash
# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Query a filesystem
mcp-bridge --server "npx @modelcontextprotocol/server-filesystem /tmp" \
  "what files are in /tmp?"

# Query git
mcp-bridge --server "uvx mcp-server-git" \
  "show me the last 3 commits"

# Use a custom model
mcp-bridge --server "python -m my_mcp_server" \
  --model claude-sonnet-4-20250514 \
  "analyze the data"
```

## How it works

1. Spawns the MCP server as a subprocess
2. Lists available tools via the MCP protocol
3. Sends your query + tool definitions to Claude
4. Claude decides which tools to call and with what arguments
5. Tool results are fed back to Claude for further reasoning
6. Returns Claude's final response

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--server`, `-s` | (required) | Command to start the MCP server |
| `--api-key` | `ANTHROPIC_API_KEY` env var | Anthropic API key |
| `--model` | `claude-sonnet-4-20250514` | Claude model |
| `--max-tokens` | 4096 | Max tokens per response |

## Disclaimer

This tool is provided for educational and research purposes. Users are responsible for API usage costs and compliance with MCP server terms of service.
