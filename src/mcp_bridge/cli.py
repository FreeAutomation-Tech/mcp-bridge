import argparse
import sys

from mcp_bridge.bridge import run_bridge, BridgeError


def main():
    parser = argparse.ArgumentParser(
        description="Bridge Claude to any MCP server via stdio"
    )
    parser.add_argument(
        "query",
        help="Natural language query to execute via MCP tools",
    )
    parser.add_argument(
        "--server",
        "-s",
        required=True,
        help="Command to start the MCP server "
             "(e.g. 'npx @modelcontextprotocol/server-filesystem .')",
    )
    parser.add_argument(
        "--api-key",
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Claude model to use (default: claude-sonnet-4-20250514)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Maximum tokens in Claude response (default: 4096)",
    )

    args = parser.parse_args()

    try:
        result = run_bridge(
            server_command=args.server,
            query=args.query,
            api_key=args.api_key,
            model=args.model,
            max_tokens=args.max_tokens,
        )
        print(result)
    except (BridgeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
