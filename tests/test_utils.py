from __future__ import annotations

from jsonschema_ts._utils import (
    _ensure_schema_has_title,
    _postprocess,
    _to_safe_name,
)


def test_to_safe_name_pascal():
    assert _to_safe_name("user_profile") == "UserProfile"


def test_to_safe_name_keeps_pascal():
    assert _to_safe_name("UserProfile") == "UserProfile"


def test_to_safe_name_special_chars():
    assert _to_safe_name("my-type!") == "MyType"


def test_to_safe_name_empty():
    assert _to_safe_name("") == "GeneratedType"


def test_to_safe_name_single_char():
    assert _to_safe_name("a") == "A"
    assert _to_safe_name("Z") == "Z"


def test_to_safe_name_all_caps():
    assert _to_safe_name("API") == "Api"


def test_to_safe_name_mixed_case():
    assert _to_safe_name("myAPIKey") == "MyApiKey"


def test_to_safe_name_with_digits():
    assert _to_safe_name("User2") == "User2"


def test_to_safe_name_purely_numeric():
    assert _to_safe_name("123") == "123"


def test_to_safe_name_acronym_in_middle():
    assert _to_safe_name("parseXML") == "ParseXml"
    assert _to_safe_name("XMLParser") == "XmlParser"


def test_ensure_schema_has_title_adds():
    schema = {"type": "object"}
    _ensure_schema_has_title(schema, "Foo")
    assert schema["title"] == "Foo"


def test_ensure_schema_has_title_preserves():
    schema = {"type": "object", "title": "Original"}
    _ensure_schema_has_title(schema, "Override")
    assert schema["title"] == "Original"


def test_postprocess_strips():
    result = _postprocess("\n  export interface Foo {}\n\n")
    assert result == "export interface Foo {}"
