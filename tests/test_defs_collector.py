from __future__ import annotations

import json
import warnings
from pathlib import Path

from jsonschema_ts._defs_collector import collect_defs

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_collect_defs_single():
    schema = load("with_defs.json")
    defs = collect_defs(schema)
    assert "Post" in defs
    assert "Author" in defs
    assert defs["Post"]["type"] == "object"
    assert defs["Author"]["type"] == "object"


def test_collect_defs_multiple():
    schema = load("with_defs.json")
    schema2 = load("nested_defs.json")
    defs = collect_defs(schema, schema2)
    assert "Post" in defs
    assert "Author" in defs
    assert "Middle" in defs
    assert "Inner" in defs


def test_collect_defs_nested():
    schema = load("nested_defs.json")
    defs = collect_defs(schema)
    assert "Inner" in defs
    assert "Middle" in defs
    assert "Outer" not in defs


def test_collect_defs_circular():
    schema = load("circular_ref.json")
    defs = collect_defs(schema)
    assert "TreeNode" in defs
    assert defs["TreeNode"]["type"] == "object"


def test_collect_defs_duplicate():
    s1 = {"$defs": {"User": {"type": "object"}}}
    s2 = {"$defs": {"User": {"type": "string"}}}
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        defs = collect_defs(s1, s2)
    assert defs["User"]["type"] == "string"
    assert len(w) == 1
    assert "Duplicate" in str(w[0].message)


def test_collect_defs_empty():
    schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
    defs = collect_defs(schema)
    assert defs == {}


def test_collect_defs_no_args():
    defs = collect_defs()
    assert defs == {}


def test_collect_defs_definitions_alias():
    schema = {"definitions": {"Foo": {"type": "object"}}}
    defs = collect_defs(schema)
    assert "Foo" in defs


def test_collect_defs_handles_lists():
    schema = {
        "type": "array",
        "items": [
            {"$defs": {"A": {"type": "object"}}},
            {"$defs": {"B": {"type": "string"}}},
        ],
    }
    defs = collect_defs(schema)
    assert "A" in defs
    assert "B" in defs


def test_collect_defs_pydantic_user():
    schema = load("pydantic_user.json")
    defs = collect_defs(schema)
    assert "Profile" in defs
    assert "User" not in defs  # User is root, not a $def
