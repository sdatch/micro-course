"""Output schema validation for generated courses."""

import json
from pathlib import Path

import jsonschema


SCHEMA_PATH = Path(__file__).parent / "prompts" / "output_schema.json"


def _load_schema() -> dict:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_course(course: dict) -> list[str]:
    """Validate a course dict against the output schema.

    Returns a list of error messages. Empty list means valid.
    """
    schema = _load_schema()
    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(course), key=lambda e: list(e.path))
    return [
        f"{'.'.join(str(p) for p in e.absolute_path) or 'root'}: {e.message}"
        for e in errors
    ]
