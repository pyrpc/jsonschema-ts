class JsonschemaTsError(Exception):
    """Base exception for all jsonschema-ts errors."""


class NodeRequiredError(JsonschemaTsError):
    """Node.js ≥ 18 with npx is not installed."""


class ConversionError(JsonschemaTsError):
    """json-schema-to-typescript failed during conversion."""
