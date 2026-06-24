import json
import subprocess

from mcp_bridge.protocol import serialize, parse_message


class McpStdioTransport:

    def __init__(self, command):
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            shell=True,
        )
        self._request_id = 0
        self._closed = False

    @property
    def alive(self):
        return self.process.poll() is None

    def send_request(self, method, params=None):
        self._request_id += 1
        msg = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params or {},
        }
        line = serialize(msg) + "\n"
        self.process.stdin.write(line)
        self.process.stdin.flush()
        return self._request_id

    def send_notification(self, method, params=None):
        msg = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
        }
        line = serialize(msg) + "\n"
        self.process.stdin.write(line)
        self.process.stdin.flush()

    def read_response(self, expected_id, timeout=None):
        while True:
            line = self.process.stdout.readline()
            if not line:
                raise ConnectionError(
                    "MCP server closed connection unexpectedly"
                )
            line = line.strip()
            if not line:
                continue
            try:
                msg = parse_message(line)
            except json.JSONDecodeError:
                continue
            if "id" in msg and msg["id"] == expected_id:
                return msg

    def close(self):
        if self._closed:
            return
        self._closed = True
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
