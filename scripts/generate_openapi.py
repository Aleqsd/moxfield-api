"""Generate the OpenAPI specification for the FastAPI app."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app  # pylint: disable=wrong-import-position


def main() -> None:
    """Write the OpenAPI schema to the repository root."""
    output_path = Path(__file__).resolve().parent.parent / "openapi.json"
    schema = app.openapi()
    output_path.write_text(json.dumps(schema, indent=2, sort_keys=True))
    print(f"OpenAPI schema written to {output_path}")  # noqa: T201


if __name__ == "__main__":
    main()
