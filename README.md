# jsonschema-ts

> **Python to TypeScript converter, powered by json-schema-to-typescript**

Convert JSON Schema (from Pydantic v2 or any source) into clean TypeScript interfaces. A thin Python wrapper around the battle-tested [`json-schema-to-typescript`](https://github.com/bcherny/json-schema-to-typescript) engine.

```python
from jsonschema_ts import convert

schema = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "email": {"type": "string", "format": "email"},
    },
    "required": ["id", "name", "email"],
}

ts = convert(schema, "User")
# export interface User {
#   id: number;
#   name: string;
#   email: string;
# }
```

## Features

- **Zero Python dependencies** — pure Python stdlib
- **Battle-tested engine** — wraps `json-schema-to-typescript`
- **Full JSON Schema support** — `$ref`, `$defs`, `allOf`, `anyOf`, `oneOf`, enums, tuples, circular refs, additional properties, const, and more
- **Pydantic v2 compatible** — works directly with `model_json_schema()` output
- **Batch conversion** — single npx call for all `$defs`
- **Clean output** — Prettier-formatted, `export interface` declarations

## Requirements

- Python ≥ 3.11
- Node.js ≥ 18 (with npx) — for the TypeScript generation engine

## Installation

```bash
pip install jsonschema-ts
```

The first call to `convert()` will prompt `npx` to cache `json-schema-to-typescript`.

## Usage

```python
from jsonschema_ts import convert, convert_all, collect_defs, ensure_inline_models

# Single schema
ts = convert(schema, "MyType")

# With $defs (for Pydantic models)
defs = collect_defs(schema)
model_ts = convert_all(defs)

# Inline models from pydantic dataclasses (@model)
schemas = ensure_inline_models(schema1, schema2)
defs = collect_defs(*schemas)
model_ts = convert_all(defs)

# Full Pydantic pipeline
from pydantic import BaseModel

class Address(BaseModel):
    street: str
    city: str
    zip: str

class User(BaseModel):
    name: str
    address: Address

schema = User.model_json_schema()
defs = collect_defs(schema)
models = convert_all(defs)
main = convert(schema, "User")
```

## API

| Function | Description |
|---|---|---|
| `convert(schema, name)` | Convert single JSON Schema → TypeScript interface |
| `convert_all(defs)` | Convert all `$defs` → TypeScript interfaces (batch) |
| `collect_defs(*schemas)` | Extract and merge `$defs` from schemas |
| `ensure_inline_models(*schemas)` | Promote inline object schemas to `$defs` entries |
| `assemble(models, procedures)` | Combine model interfaces + procedure types into final TS output |
| `ensure_npx()` | Check Node.js/npx availability |

```python
from jsonschema_ts import collect_defs, convert, convert_all, ensure_inline_models, assemble

# ... promote inline models, then collect and convert ...
schemas = ensure_inline_models(raw_schema)
defs = collect_defs(*schemas)
models = convert_all(defs)

# Combine everything into final output
output = assemble(
    models=models,
    procedures="export interface Types { greet(name: string): Promise<string>; }",
)
```

## Why a wrapper?

`json-schema-to-typescript` has an **8-stage pipeline** (resolver → linker → normalizer → parser → optimizer → generator → formatter) with 18 normalization rules handling hundreds of edge cases. Reimplementing this in Python would take months. This package delegates the heavy lifting and focuses on what Python does best: orchestration, `$defs` collection, and output assembly.

## License

MIT
