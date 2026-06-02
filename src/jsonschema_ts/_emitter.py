from __future__ import annotations

from jsonschema_ts._utils import DEFAULT_BANNER


def assemble(models: str, procedures: str, banner: str = DEFAULT_BANNER) -> str:
    parts: list[str] = []
    if banner:
        parts.append(banner.strip())
    if models.strip():
        parts.append("// ── Models ──────────────────────────────────────────────")
        parts.append(models.strip())
    if procedures.strip():
        parts.append("// ── Procedures ──────────────────────────────────────────")
        parts.append(procedures.strip())
    return "\n\n".join(parts)


def _strip_root_interface(ts_code: str, root_name: str = "__ROOT__") -> str:
    lines = ts_code.split("\n")
    filtered: list[str] = []
    skip = False
    for line in lines:
        if line.strip().startswith(f"export interface {root_name}"):
            skip = True
            continue
        if skip:
            if line.strip() == "":
                skip = False
                continue
            if line.strip().startswith("export interface"):
                skip = False
        if not skip:
            filtered.append(line)
    return "\n".join(filtered).strip()
