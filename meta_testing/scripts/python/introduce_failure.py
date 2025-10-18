"""Utility to inject a deterministic failing test into the sample project."""

from __future__ import annotations

import argparse
import pathlib

FAILURE_SNIPPET = """

def test_forced_meta_failure() -> None:
    \"\"\"Fail intentionally so regression detection can be rehearsed.\"\"\"
    raise AssertionError(\"Meta-testing injected failure\")
"""

MARKER = "test_forced_meta_failure"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target",
        type=pathlib.Path,
        help="Path to the test module that should receive the forced failure.",
    )
    args = parser.parse_args()

    target_path = args.target.resolve()
    if not target_path.exists():
        raise FileNotFoundError(
            f"Cannot introduce failure into missing file: {target_path}"
        )

    contents = target_path.read_text()
    if MARKER in contents:
        # Idempotent runs should not duplicate the failure block.
        return

    target_path.write_text(f"{contents.rstrip()}\n{FAILURE_SNIPPET}")


if __name__ == "__main__":
    main()
