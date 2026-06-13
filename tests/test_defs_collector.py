from __future__ import annotations

import json
import warnings
from pathlib import Path

from jsonschema_ts._defs_collector import collect_defs, ensure_inline_models

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


# ── ensure_inline_models tests ───────────────────────────────────


def test_ensure_inline_models_promotes_root():
    schema = load("inline_model.json")
    result = ensure_inline_models(schema)
    assert len(result) == 1
    modified = result[0]
    assert "$ref" in modified
    assert modified["$ref"] == "#/$defs/CreateUserInput"
    assert "$defs" in modified
    assert "CreateUserInput" in modified["$defs"]
    assert modified["$defs"]["CreateUserInput"]["type"] == "object"


def test_ensure_inline_models_nested():
    schema = load("inline_nested.json")
    result = ensure_inline_models(schema)
    assert len(result) == 1
    modified = result[0]
    assert modified["$ref"] == "#/$defs/Outer"
    assert "Inner" in modified["$defs"]
    assert "Outer" in modified["$defs"]
    assert modified["$defs"]["Outer"]["properties"]["inner"]["$ref"] == "#/$defs/Inner"


def test_ensure_inline_models_skips_existing_defs():
    schema = load("pydantic_user.json")
    result = ensure_inline_models(schema)
    assert len(result) == 1
    modified = result[0]
    assert modified["$ref"] == "#/$defs/User"
    assert "User" in modified["$defs"]
    assert "Profile" in modified["$defs"]["User"]["$defs"]
    assert "$defs" not in modified["$defs"]["User"]["$defs"]["Profile"]


def test_ensure_inline_models_no_title():
    schema = {
        "type": "object",
        "properties": {"x": {"type": "integer"}},
    }
    result = ensure_inline_models(schema)
    assert len(result) == 1
    assert "$ref" not in result[0]
    assert "$defs" not in result[0]


def test_ensure_inline_models_multiple():
    s1 = {"title": "A", "type": "object", "properties": {"x": {"type": "integer"}}}
    s2 = {"title": "B", "type": "object", "properties": {"y": {"type": "string"}}}
    result = ensure_inline_models(s1, s2)
    assert len(result) == 2
    assert result[0]["$ref"] == "#/$defs/A"
    assert result[1]["$ref"] == "#/$defs/B"
    assert "A" in result[0]["$defs"]
    assert "B" in result[1]["$defs"]


def test_ensure_inline_models_no_args():
    result = ensure_inline_models()
    assert result == []


def test_ensure_inline_models_does_not_mutate_input():
    schema = {"title": "Test", "type": "object", "properties": {}}
    original = dict(schema)
    ensure_inline_models(schema)
    assert schema == original


def test_ensure_inline_with_collect_defs_integration():
    schema = load("inline_model.json")
    promoted = ensure_inline_models(schema)
    defs = collect_defs(*promoted)
    assert "CreateUserInput" in defs
