"""Compatibility shims for CrewAI's MCP tool-schema conversion.

CrewAI 1.15.x's ``_json_schema_to_pydantic_type`` only understands a scalar
``type`` field. MCP servers (e.g. PageIndex) legitimately declare nullable
parameters using JSON Schema's list form, ``{"type": ["string", "null"]}``,
which makes the adapter raise ``Unsupported JSON schema type``. This shim
normalises list-typed schemas into ``Optional[...]`` before delegating to the
original converter.
"""

from typing import Any, Optional

_PATCH_APPLIED = False


def apply_nullable_schema_patch() -> None:
    """Idempotently patch CrewAI to accept list-typed (nullable) JSON schemas."""
    global _PATCH_APPLIED
    if _PATCH_APPLIED:
        return

    from crewai.utilities import pydantic_schema_utils as psu

    original = psu._json_schema_to_pydantic_type

    def patched(json_schema, *args, **kwargs):
        type_ = json_schema.get("type") if isinstance(json_schema, dict) else None
        if isinstance(type_, list):
            non_null = [t for t in type_ if t != "null"]
            nullable = "null" in type_
            new_schema = dict(json_schema)

            if len(non_null) == 1:
                new_schema["type"] = non_null[0]
            elif not non_null:
                new_schema["type"] = "null"
            else:
                # Multiple concrete types (a true union) — no single pydantic
                # type fits, so fall back to Any.
                new_schema.pop("type", None)
                return Optional[Any] if nullable else Any

            inner = patched(new_schema, *args, **kwargs)
            if nullable and inner is not None:
                return Optional[inner]
            return inner

        return original(json_schema, *args, **kwargs)

    psu._json_schema_to_pydantic_type = patched
    _PATCH_APPLIED = True
