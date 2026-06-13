from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from jsonschema_ts import ConversionError, Options, convert, convert_all
from jsonschema_ts._converter import _build_daemon_options, _to_npx

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


MOCK_TS = """
export interface User {
  name: string;
  age: number;
}
""".strip()


# ── Unit tests (mocked npx) ──────────────────────────────────────


@patch("jsonschema_ts._converter._to_npx", return_value=MOCK_TS)
def test_convert_basic(mock_to_npx):
    schema = {"type": "object", "properties": {"name": {"type": "string"}}}
    result = convert(schema, "User")
    assert "export interface User" in result
    assert "name: string" in result


@patch("jsonschema_ts._converter._to_npx", return_value=MOCK_TS)
def test_convert_injects_title(mock_to_npx):
    schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
    convert(schema, "Foo")
    args, _ = mock_to_npx.call_args
    assert args[0]["title"] == "Foo"


@patch("jsonschema_ts._converter._to_npx")
def test_convert_passes_opts(mock_to_npx):
    mock_to_npx.return_value = "export interface X { x: number; }"
    opts = Options(unknown_any=False, format=False)
    convert({"type": "object"}, "X", opts=opts)
    args, _ = mock_to_npx.call_args
    assert args[1] is opts


@patch("jsonschema_ts._converter._to_npx")
def test_convert_all_empty(mock_to_npx):
    result = convert_all({})
    assert result == ""
    mock_to_npx.assert_not_called()


@patch("jsonschema_ts._converter._to_npx")
def test_convert_all_with_defs(mock_to_npx):
    mock_to_npx.return_value = """
export interface Post {
  title: string;
}

export interface Author {
  name: string;
}

export interface __ROOT__ {
  _Post_ref: Post;
  _Author_ref: Author;
}
""".strip()
    defs = {
        "Post": {"type": "object", "properties": {"title": {"type": "string"}}},
        "Author": {"type": "object", "properties": {"name": {"type": "string"}}},
    }
    result = convert_all(defs)
    assert "export interface Post" in result
    assert "export interface Author" in result
    assert "__ROOT__" not in result


@patch("jsonschema_ts._converter._to_npx")
def test_convert_all_injects_titles(mock_to_npx):
    mock_to_npx.return_value = """
export interface Foo {
  x: number;
}
""".strip()
    defs = {"Foo": {"type": "object", "properties": {"x": {"type": "integer"}}}}
    result = convert_all(defs)
    assert "Foo" in result


@patch("jsonschema_ts._converter._to_npx", side_effect=ConversionError("fail"))
def test_convert_raises_conversion_error(mock_to_npx):
    with pytest.raises(ConversionError, match="fail"):
        convert({"type": "object"}, "Bad")



# ── Daemon integration tests (mocked daemon layer) ────────────────


@patch("jsonschema_ts._converter.daemon_convert")
def test_to_npx_tries_daemon_first(mock_daemon_convert):
    mock_daemon_convert.return_value = MOCK_TS
    opts = Options(use_daemon=True)
    schema = {"type": "object", "title": "User"}
    result = _to_npx(schema, opts)
    assert result == MOCK_TS
    mock_daemon_convert.assert_called_once()
    call_schema, call_opts = mock_daemon_convert.call_args[0]
    assert call_schema == schema
    assert call_opts["unknownAny"] is True


@patch("jsonschema_ts._converter._to_npx_subprocess")
def test_to_npx_skips_daemon_when_disabled(mock_subprocess):
    mock_subprocess.return_value = MOCK_TS
    opts = Options(use_daemon=False)
    schema = {"type": "object", "title": "User"}
    result = _to_npx(schema, opts)
    assert result == MOCK_TS
    mock_subprocess.assert_called_once_with(schema, opts)


@patch(
    "jsonschema_ts._converter.daemon_convert",
    side_effect=ConnectionError("daemon down"),
)
@patch("jsonschema_ts._converter._to_npx_subprocess")
def test_to_npx_falls_back_on_daemon_error(mock_subprocess, mock_daemon_convert):
    mock_subprocess.return_value = MOCK_TS
    opts = Options(use_daemon=True)
    schema = {"type": "object", "title": "User"}
    result = _to_npx(schema, opts)
    assert result == MOCK_TS
    mock_daemon_convert.assert_called_once()
    mock_subprocess.assert_called_once_with(schema, opts)


@patch(
    "jsonschema_ts._converter.daemon_convert",
    side_effect=ConversionError("daemon fail"),
)
@patch("jsonschema_ts._converter._to_npx_subprocess")
def test_to_npx_falls_back_on_conversion_error(mock_subprocess, mock_daemon_convert):
    mock_subprocess.return_value = MOCK_TS
    opts = Options(use_daemon=True)
    result = _to_npx({"type": "object", "title": "User"}, opts)
    assert result == MOCK_TS
    mock_subprocess.assert_called_once()


@patch(
    "jsonschema_ts._converter.daemon_convert",
    side_effect=ConversionError("fail"),
)
@patch(
    "jsonschema_ts._converter._to_npx_subprocess",
    side_effect=ConversionError("subprocess also fail"),
)
def test_to_npx_raises_when_both_fail(mock_subprocess, mock_daemon_convert):
    opts = Options(use_daemon=True)
    with pytest.raises(ConversionError, match="subprocess also fail"):
        _to_npx({"type": "object", "title": "User"}, opts)


def test_build_daemon_options():
    opts = Options(
        banner_comment="custom banner",
        format=False,
        unknown_any=False,
        unreachable_definitions=False,
    )
    result = _build_daemon_options(opts)
    assert result["bannerComment"] == "custom banner"
    assert result["format"] is False
    assert result["unknownAny"] is False
    assert result["unreachableDefinitions"] is False


def test_build_daemon_options_defaults():
    opts = Options()
    result = _build_daemon_options(opts)
    assert result["bannerComment"] == opts.banner_comment
    assert result["format"] is True
    assert result["unknownAny"] is True
    assert result["unreachableDefinitions"] is True


@patch("jsonschema_ts._converter.daemon_convert")
def test_convert_uses_daemon_by_default(mock_daemon_convert):
    mock_daemon_convert.return_value = MOCK_TS
    schema = {"type": "object", "properties": {"name": {"type": "string"}}}
    result = convert(schema, "User")
    assert "export interface User" in result
    mock_daemon_convert.assert_called_once()


@patch("jsonschema_ts._converter._to_npx_subprocess")
def test_convert_use_daemon_false_skips_daemon(mock_subprocess):
    mock_subprocess.return_value = MOCK_TS
    opts = Options(use_daemon=False)
    schema = {"type": "object", "properties": {"name": {"type": "string"}}}
    convert(schema, "User", opts=opts)
    mock_subprocess.assert_called_once()


@patch("jsonschema_ts._converter.daemon_convert")
def test_convert_sets_title_before_daemon(mock_daemon_convert):
    mock_daemon_convert.return_value = MOCK_TS
    schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
    convert(schema, "Foo")
    call_schema, _ = mock_daemon_convert.call_args[0]
    assert call_schema["title"] == "Foo"


# ── Integration tests (require npx) ──────────────────────────────


@pytest.mark.integration
def test_integration_convert_simple_object():
    schema = load("simple_object.json")
    result = convert(schema, "SimpleObject")
    assert "export interface SimpleObject" in result
    assert "name: string" in result
    assert "age: number" in result
    assert "score: number" in result
    assert "active: boolean" in result


@pytest.mark.integration
def test_integration_convert_with_defs():
    schema = load("with_defs.json")
    result = convert(schema, "Blog")
    assert "export interface Blog" in result
    assert "posts: Post" in result or "posts?: Post" in result


@pytest.mark.integration
def test_integration_convert_all():
    schema = load("with_defs.json")
    from jsonschema_ts._defs_collector import collect_defs

    defs = collect_defs(schema)
    result = convert_all(defs)
    assert "export interface Post" in result
    assert "export interface Author" in result


@pytest.mark.integration
def test_integration_deterministic():
    schema = load("simple_object.json")
    r1 = convert(schema, "SimpleObject")
    r2 = convert(schema, "SimpleObject")
    assert r1 == r2
