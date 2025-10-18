"""Append an intentionally failing xUnit test to the sample suite."""

from __future__ import annotations

import argparse
import pathlib

FAILURE_SNIPPET = """

    [Fact]
    public void MetaInjectedFailure()
    {
        Assert.True(false, "Meta-testing injected failure");
    }
"""

MARKER = "MetaInjectedFailure"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target",
        type=pathlib.Path,
        help="Path to the test file that should receive the forced failure.",
    )
    args = parser.parse_args()

    target_path = args.target.resolve()
    if not target_path.exists():
        raise FileNotFoundError(
            f"Cannot introduce failure into missing file: {target_path}"
        )

    contents = target_path.read_text()
    if MARKER in contents:
        return

    target_path.write_text(contents.replace("}\n}", f"{FAILURE_SNIPPET}\n}}"))


if __name__ == "__main__":
    main()
