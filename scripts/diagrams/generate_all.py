"""Entry point for `npm run diagrams`.

Runs every diagram module's `build()` function, writing deterministic SVGs
into public/diagrams/. To add a new diagram, see scripts/diagrams/README.md.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import order_state_machine  # noqa: E402  (must follow the sys.path insert above)

DIAGRAM_MODULES = [order_state_machine]


def main() -> None:
    for module in DIAGRAM_MODULES:
        start = time.monotonic()
        module.build()
        elapsed_ms = (time.monotonic() - start) * 1000
        print(f"  generated {module.OUTPUT_NAME}.svg ({elapsed_ms:.0f}ms)")

    print(f"Generated {len(DIAGRAM_MODULES)} diagram(s) into public/diagrams/.")


if __name__ == "__main__":
    main()
