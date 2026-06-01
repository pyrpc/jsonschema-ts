from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from jsonschema_ts import ConversionError, Options, convert, convert_all

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
