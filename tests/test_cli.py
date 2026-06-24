import pytest

from mcp_bridge.cli import main


class TestCli:

    def test_requires_server(self, mocker):
        mocker.patch("sys.argv", ["mcp-bridge"])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code != 0

    def test_requires_query(self, mocker):
        mocker.patch("sys.argv", ["mcp-bridge", "--server", "echo"])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code != 0
