import pytest

from mcp_bridge.transport import McpStdioTransport


class TestMcpStdioTransport:

    def test_process_dies(self, mocker):
        mock_proc = mocker.Mock()
        mock_proc.poll.return_value = None
        mock_proc.stdout.readline.return_value = ""
        mocker.patch(
            "mcp_bridge.transport.subprocess.Popen",
            return_value=mock_proc,
        )

        transport = McpStdioTransport("echo test")
        with pytest.raises(ConnectionError):
            transport.read_response(1)

    def test_alive_property(self, mocker):
        mock_proc = mocker.Mock()
        mock_proc.poll.return_value = None
        mocker.patch(
            "mcp_bridge.transport.subprocess.Popen",
            return_value=mock_proc,
        )

        transport = McpStdioTransport("echo test")
        assert transport.alive is True

    def test_close(self, mocker):
        mock_proc = mocker.Mock()
        mock_proc.poll.return_value = None
        mocker.patch(
            "mcp_bridge.transport.subprocess.Popen",
            return_value=mock_proc,
        )

        transport = McpStdioTransport("echo test")
        transport.close()
        assert transport._closed is True

    def test_context_manager(self, mocker):
        mock_proc = mocker.Mock()
        mock_proc.poll.return_value = None
        mocker.patch(
            "mcp_bridge.transport.subprocess.Popen",
            return_value=mock_proc,
        )

        with McpStdioTransport("echo test") as transport:
            assert transport.alive is True

    def test_dead_process(self, mocker):
        mock_proc = mocker.Mock()
        mock_proc.poll.return_value = 1
        mocker.patch(
            "mcp_bridge.transport.subprocess.Popen",
            return_value=mock_proc,
        )

        transport = McpStdioTransport("echo test")
        assert transport.alive is False
