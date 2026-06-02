from jsonschema_ts._converter import convert, convert_all
from jsonschema_ts._defs_collector import collect_defs
from jsonschema_ts._emitter import assemble
from jsonschema_ts._errors import ConversionError, JsonschemaTsError, NodeRequiredError
from jsonschema_ts._options import Options
from jsonschema_ts._utils import _ensure_npx

__version__ = "0.1.1"

__all__ = [
    "convert",
    "convert_all",
    "collect_defs",
    "assemble",
    "ensure_npx",
    "Options",
    "JsonschemaTsError",
    "NodeRequiredError",
    "ConversionError",
    "__version__",
]


def ensure_npx() -> None:
    _ensure_npx()
