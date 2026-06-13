from __future__ import annotations

import copy
import warnings
from typing import Any


def collect_defs(*schemas: dict) -> dict[str, dict]:
    collected: dict[str, dict] = {}
    seen: set[int] = set()

    for schema in schemas:
        _walk_node(schema, collected, seen)

    return collected


def _walk_node(node: Any, collected: dict[str, dict], seen: set[int]) -> None:
    if id(node) in seen:
        return
    seen.add(id(node))

    if isinstance(node, dict):
        for key, value in list(node.items()):
            if key in ("$defs", "definitions"):
                for def_name, def_schema in value.items():
                    if def_name in collected:
                        warnings.warn(
                            f"Duplicate $def '{def_name}' — using last definition",
                            stacklevel=2,
                        )
                    collected[def_name] = def_schema
                    _walk_node(def_schema, collected, seen)
            else:
                _walk_node(value, collected, seen)
    elif isinstance(node, list):
        for item in node:
            _walk_node(item, collected, seen)


def ensure_inline_models(*schemas: dict) -> list[dict]:
    result: list[dict] = []
    for schema in schemas:
        schema_copy = copy.deepcopy(schema)
        root_defs: dict[str, dict] = {}
        processed = _walk_and_promote(schema_copy, root_defs, in_defs=False)
        if root_defs:
            if "$defs" not in processed:
                processed["$defs"] = {}
            processed["$defs"].update(root_defs)
        result.append(processed)
    return result


def _walk_and_promote(node: Any, root_defs: dict[str, dict], in_defs: bool) -> Any:
    if isinstance(node, dict):
        if (
            not in_defs
            and node.get("type") == "object"
            and isinstance(node.get("title"), str)
        ):
            title = node["title"]
            if title not in root_defs:
                promoted: dict[str, Any] = {}
                for k, v in node.items():
                    if k in ("$defs", "definitions"):
                        promoted[k] = {
                            dk: _walk_and_promote(dv, root_defs, True)
                            for dk, dv in v.items()
                        }
                    else:
                        promoted[k] = _walk_and_promote(v, root_defs, False)
                root_defs[title] = promoted
            return {"$ref": f"#/$defs/{title}"}

        return {
            k: _walk_and_promote(
                v,
                root_defs,
                in_defs or k in ("$defs", "definitions"),
            )
            for k, v in node.items()
        }
    elif isinstance(node, list):
        return [_walk_and_promote(item, root_defs, in_defs) for item in node]
    return node
