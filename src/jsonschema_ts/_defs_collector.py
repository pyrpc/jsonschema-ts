from __future__ import annotations

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
