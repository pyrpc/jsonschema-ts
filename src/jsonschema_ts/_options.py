from dataclasses import dataclass

from jsonschema_ts._utils import DEFAULT_BANNER


@dataclass
class Options:
    banner_comment: str = DEFAULT_BANNER
    format: bool = True
    unknown_any: bool = True
    unreachable_definitions: bool = True
    npx_cache: str | None = None
