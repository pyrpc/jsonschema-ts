from __future__ import annotations

import json
import threading
from unittest.mock import MagicMock, patch

import pytest

from jsonschema_ts._errors import ConversionError
from jsonschema_ts._npx_daemon import _NPXDaemon, stop
from jsonschema_ts._npx_daemon import convert as daemon_convert


def _mock_ensure_package(return_value="/fake/node_modules"):
    return patch.object(_NPXDaemon, "_ensure_package", return_value=return_value)


def test_daemon_start_creates_process():
    daemon = _NPXDaemon()
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None

    with _mock_ensure_package():
        with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
            daemon.start()
            mock_popen.assert_called_once()
            args = mock_popen.call_args[0][0]
            assert args[0] == "node"
            assert "_npx_daemon.js" in args[-1]

    daemon.stop()


def test_daemon_start_sets_cache_env():
    daemon = _NPXDaemon()
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    fake_path = "/custom/node_modules"

    with patch.object(_NPXDaemon, "_ensure_package", return_value=fake_path):
        with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
            daemon.start()
            env = mock_popen.call_args[1].get("env", {})
            assert env.get("JSONSCHEMA_TS_CACHE") == fake_path

    daemon.stop()


def test_daemon_start_reuses_existing():
    daemon = _NPXDaemon()
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None

    with _mock_ensure_package():
        with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
            daemon.start()
            daemon.start()
            mock_popen.assert_called_once()

    daemon.stop()


def test_daemon_start_restarts_dead_process():
    daemon = _NPXDaemon()
    mock_proc = MagicMock()
    mock_proc.poll.return_value = 0

    with _mock_ensure_package():
        with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
            daemon.start()
            daemon.start()
            assert mock_popen.call_count == 2

    daemon.stop()


def test_daemon_ensure_package_installs_when_missing():
    daemon = _NPXDaemon()
    with patch("subprocess.run") as mock_run:
        with patch("pathlib.Path.mkdir"):
            with patch("pathlib.Path.is_dir") as mock_is_dir:
                mock_is_dir.side_effect = [False, True]
                result = daemon._ensure_package()
                mock_run.assert_called_once()
                args = mock_run.call_args[0][0]
                assert "npm" in args[0] or "npm.cmd" in args[0]
                assert "install" in args
                assert "json-schema-to-typescript" in args
                assert result is not None


def test_daemon_ensure_package_returns_none_on_failure():
    daemon = _NPXDaemon()
    with patch("subprocess.run", side_effect=Exception("npm failed")):
        with patch("pathlib.Path.mkdir"):
            with patch("pathlib.Path.is_dir") as mock_is_dir:
                mock_is_dir.side_effect = [False, False]
                result = daemon._ensure_package()
                assert result is None


def test_daemon_ensure_package_skips_when_cached():
    daemon = _NPXDaemon()
    with patch("subprocess.run") as mock_run:
        with patch("pathlib.Path.is_dir", return_value=True):
            result = daemon._ensure_package()
            mock_run.assert_not_called()
            assert result is not None


def test_daemon_convert_sends_and_receives():
    daemon = _NPXDaemon()
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    mock_proc.stdin = MagicMock()
    mock_proc.stdout = MagicMock()
    expected_ts = "export interface Foo { bar: string; }"
    mock_proc.stdout.readline.return_value = (
        json.dumps({"success": True, "data": expected_ts}) + "\n"
    )

    with _mock_ensure_package():
        with patch("subprocess.Popen", return_value=mock_proc):
            result = daemon.convert({"type": "object"}, {})

    assert result == expected_ts
    sent_msg = mock_proc.stdin.write.call_args[0][0]
    sent_data = json.loads(sent_msg.strip())
    assert sent_data["schema"] == {"type": "object"}
    assert sent_data["options"] == {}

    daemon.stop()


def test_daemon_convert_passes_options():
    daemon = _NPXDaemon()
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    mock_proc.stdin = MagicMock()
    mock_proc.stdout = MagicMock()
    mock_proc.stdout.readline.return_value = (
        json.dumps({"success": True, "data": "ts code"}) + "\n"
    )

    daemon_opts = {"unknownAny": False, "bannerComment": "custom"}
    with _mock_ensure_package():
        with patch("subprocess.Popen", return_value=mock_proc):
            daemon.convert({"type": "object"}, daemon_opts)

    sent_msg = mock_proc.stdin.write.call_args[0][0]
    sent_data = json.loads(sent_msg.strip())
    assert sent_data["options"] == daemon_opts

    daemon.stop()


def test_daemon_convert_error_response():
    daemon = _NPXDaemon()
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    mock_proc.stdin = MagicMock()
    mock_proc.stdout = MagicMock()
    mock_proc.stdout.readline.return_value = (
        json.dumps({"success": False, "error": "bad schema"}) + "\n"
    )

    with _mock_ensure_package():
        with patch("subprocess.Popen", return_value=mock_proc):
            with pytest.raises(ConversionError, match="bad schema"):
                daemon.convert({"type": "bad"}, {})

    daemon.stop()


def test_daemon_convert_connection_closed():
    daemon = _NPXDaemon()
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    mock_proc.stdin = MagicMock()
    mock_proc.stdout = MagicMock()
    mock_proc.stdout.readline.return_value = ""

    with _mock_ensure_package():
        with patch("subprocess.Popen", return_value=mock_proc):
            with pytest.raises(ConnectionError, match="closed connection"):
                daemon.convert({"type": "object"}, {})

    daemon.stop()


def test_daemon_stop_terminates_process():
    daemon = _NPXDaemon()
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    mock_proc.stdin = MagicMock()
    mock_proc.stdout = MagicMock()

    with _mock_ensure_package():
        with patch("subprocess.Popen", return_value=mock_proc):
            daemon.start()
            daemon.stop()
            mock_proc.terminate.assert_called_once()
            mock_proc.wait.assert_called_once_with(timeout=5)


def test_daemon_stop_already_dead():
    daemon = _NPXDaemon()
    mock_proc = MagicMock()
    mock_proc.poll.return_value = 0
    mock_proc.stdin = MagicMock()
    mock_proc.stdout = MagicMock()

    with _mock_ensure_package():
        with patch("subprocess.Popen", return_value=mock_proc):
            daemon.start()
            daemon.stop()
            mock_proc.terminate.assert_not_called()


def test_daemon_stop_no_process():
    daemon = _NPXDaemon()
    daemon.stop()


def test_daemon_convert_is_thread_safe():
    daemon = _NPXDaemon()
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    mock_proc.stdin = MagicMock()
    mock_proc.stdout = MagicMock()
    mock_proc.stdout.readline.return_value = (
        json.dumps({"success": True, "data": "ts"}) + "\n"
    )

    results: list[str] = []
    errors: list[Exception] = []

    def call_convert():
        with _mock_ensure_package():
            with patch("subprocess.Popen", return_value=mock_proc):
                try:
                    results.append(daemon.convert({"type": "object"}, {}))
                except Exception as e:
                    errors.append(e)

    threads = [threading.Thread(target=call_convert) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(results) == 5

    daemon.stop()


def test_daemon_singleton_module_convert():
    stop()

    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    mock_proc.stdin = MagicMock()
    mock_proc.stdout = MagicMock()
    expected_ts = "export interface Test { x: number; }"
    mock_proc.stdout.readline.return_value = (
        json.dumps({"success": True, "data": expected_ts}) + "\n"
    )

    with _mock_ensure_package():
        with patch("subprocess.Popen", return_value=mock_proc):
            result = daemon_convert({"type": "object"}, {})

    assert result == expected_ts
    stop()


@pytest.mark.integration
def test_daemon_integration_real_subprocess():
    stop()
    try:
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        result = daemon_convert(
            schema, {"unknownAny": True, "unreachableDefinitions": True}
        )
        assert "export interface Root" in result
        assert "name?: string" in result
    finally:
        stop()
