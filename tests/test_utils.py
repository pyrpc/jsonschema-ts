from __future__ import annotations

from jsonschema_ts._errors import NodeRequiredError
from jsonschema_ts._utils import _ensure_npx, _ensure_schema_has_title, _postprocess, _to_safe_name


def test_to_safe_name_pascal():
    assert _to_safe_name("user_profile") == "UserProfile"


def test_to_safe_name_keeps_pascal():
    assert _to_safe_name("UserProfile") == "Userprofile"


def test_to_safe_name_special_chars():
    assert _to_safe_name("my-type!") == "MyType"


def test_to_safe_name_empty():
    assert _to_safe_name("") == "GeneratedType"


def test_ensure_schema_has_title_adds():
    schema = {"type": "object"}
    _ensure_schema_has_title(schema, "Foo")
    assert schema["title"] == "Foo"


def test_ensure_schema_has_title_preserves():
    schema = {"type": "object", "title": "Original"}
    _ensure_schema_has_title(schema, "Override")
    assert schema["title"] == "Original"


def test_postprocess_strips():
    result = _postprocess("\n  export interface Foo {}\n\n", "Foo")
    assert result == "export interface Foo {}"
