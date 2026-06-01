from __future__ import annotations

import json
import os
import subprocess
import tempfile
from typing import Any

from jsonschema_ts._emitter import _strip_root_interface
from jsonschema_ts._errors import ConversionError
from jsonschema_ts._options import Options
from jsonschema_ts._utils import _ensure_npx, _ensure_schema_has_title, _postprocess, _to_safe_name


NPX_ARGS_BASE = [
    "npx",
    "--package=json-schema-to-typescript",
    "json2ts",
    "--unreachableDefinitions",
]


def convert(schema: dict, name: str, opts: Options | None = None) -> str:
    opts = opts or Options()
    _ensure_schema_has_title(schema, name)
    ts_code = _to_npx(schema, opts)
    return _postprocess(ts_code, name)


def convert_all(defs: dict[str, dict], opts: Options | None = None) -> str:
    opts = opts or Options()
    if not defs:
        return ""

    combined: dict[str, Any] = {
        "title": "__ROOT__",
        "type": "object",
        "properties": {},
        "$defs": {},
    }

    for name, schema in defs.items():
        safe_name = _to_safe_name(name)
        combined["$defs"][safe_name] = dict(schema)
        if "title" not in combined["$defs"][safe_name]:
            combined["$defs"][safe_name]["title"] = safe_name
        combined["properties"][f"_{safe_name}_ref"] = {"$ref": f"#/$defs/{safe_name}"}

    ts_code = _to_npx(combined, opts)
    return _strip_root_interface(ts_code)


def _to_npx(schema: dict, opts: Options) -> str:
    _ensure_npx()

    npx_args = list(NPX_ARGS_BASE)
    if opts.unknown_any:
        npx_args.append("--unknownAny")

    env = os.environ.copy()
    if opts.npx_cache:
        env.setdefault("npm_config_cache", opts.npx_cache)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(schema, f, indent=2)
        f.flush()
        temp_path = f.name

    npx_args.append(temp_path)

    try:
        result = subprocess.run(
            npx_args,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
            env=env,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise ConversionError(
            f"json-schema-to-typescript failed (exit {e.returncode}).\n"
            f"Stderr: {e.stderr.strip()}"
        ) from e
    except subprocess.TimeoutExpired:
        raise ConversionError("json-schema-to-typescript timed out after 30s.")
    finally:
        os.unlink(temp_path)
