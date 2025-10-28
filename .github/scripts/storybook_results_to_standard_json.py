#!/usr/bin/env python3
"""Normalize Storybook test results into the shared regression JSON format."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterator, List, MutableMapping, Optional, Sequence, Tuple

PASS_STATUSES: Tuple[str, ...] = (
    "passed",
    "pass",
    "success",
)
FAIL_STATUSES: Tuple[str, ...] = (
    "failed",
    "fail",
    "error",
    "broken",
    "timedout",
    "timed_out",
)
SKIP_STATUSES: Tuple[str, ...] = (
    "skipped",
    "skip",
    "pending",
    "todo",
    "disabled",
)
XFAIL_STATUSES: Tuple[str, ...] = (
    "xfailed",
    "xfail",
    "expected_fail",
)


def _normalise_status(raw: Optional[str]) -> str:
    if not raw:
        return "unknown"
    return str(raw).strip().lower().replace(" ", "_")


def _format_name(
    entry: MutableMapping[str, object], fallback: Optional[str] = None
) -> str:
    for key in ("fullName", "full_name", "name", "title"):
        value = entry.get(key)
        if value:
            return str(value)

    ancestors = entry.get("ancestorTitles") or entry.get("ancestor_titles")
    ancestor_str = ""
    if isinstance(ancestors, Sequence) and not isinstance(ancestors, (str, bytes)):
        ancestor_parts = [str(part) for part in ancestors if part]
        if ancestor_parts:
            ancestor_str = " :: ".join(ancestor_parts)
    elif ancestors:
        ancestor_str = str(ancestors)

    title = entry.get("title") or entry.get("name")
    title_str = str(title) if title else ""

    if ancestor_str and title_str:
        return f"{ancestor_str} :: {title_str}"

    if title_str:
        return title_str

    if fallback:
        return fallback

    return ""


def _iter_test_entries(
    payload: object, fallback: Optional[str] = None
) -> Iterator[Tuple[str, str]]:
    if isinstance(payload, dict):
        assertion_results = payload.get("assertionResults")
        if isinstance(assertion_results, list):
            base = (
                payload.get("name")
                or payload.get("file")
                or payload.get("testFilePath")
                or payload.get("test_file_path")
                or fallback
            )
            base_str = str(base) if base else None
            for assertion in assertion_results:
                if isinstance(assertion, dict):
                    name = _format_name(assertion, base_str)
                    status = _normalise_status(
                        assertion.get("status") or assertion.get("outcome")
                    )
                    if name:
                        yield name, status
            return

        nested_keys = ("tests", "testResults", "results", "suites", "children")
        handled_nested = False
        for key in nested_keys:
            nested = payload.get(key)
            if isinstance(nested, list):
                handled_nested = True
                for item in nested:
                    yield from _iter_test_entries(item, fallback)

        if not handled_nested:
            name = _format_name(payload, fallback)
            status = _normalise_status(
                payload.get("status") or payload.get("outcome") or payload.get("result")
            )
            if name or status != "unknown":
                yield name, status

    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_test_entries(item, fallback)


def _collect_tests(payload: object) -> Dict[str, List[str]]:
    passing: List[str] = []
    failing: List[str] = []
    skipped: List[str] = []
    xfailed: List[str] = []
    other: List[str] = []

    seen: set[str] = set()

    for name, status in _iter_test_entries(payload):
        name = name.strip()
        if not name or name in seen:
            continue
        seen.add(name)

        if status in PASS_STATUSES:
            passing.append(name)
        elif status in FAIL_STATUSES:
            failing.append(name)
        elif status in SKIP_STATUSES:
            skipped.append(name)
        elif status in XFAIL_STATUSES:
            xfailed.append(name)
        else:
            other.append(name)

    all_items = sorted({*passing, *failing, *skipped, *xfailed, *other})

    return {
        "passing_tests": sorted(passing),
        "failing_tests": sorted(failing),
        "skipped_tests": sorted(skipped),
        "xfailed_tests": sorted(xfailed),
        "all_tests": all_items,
        "other_tests": sorted(other),
    }


def _load_payload(path: Path) -> object:
    if not path.exists():
        return {}
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return {}
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        print(f"::warning::Failed to parse JSON from {path}: {exc}", file=sys.stderr)
        return {}


def _extract_warnings(payload: object) -> List[str]:
    if isinstance(payload, dict):
        warnings = payload.get("warnings")
        if isinstance(warnings, list):
            return [str(item) for item in warnings if item]
    return []


def normalise_results(input_path: Path, output_path: Path) -> Dict[str, object]:
    payload = _load_payload(input_path)
    tests = _collect_tests(payload)
    warnings = _extract_warnings(payload)

    total = len(tests["all_tests"])
    passed = len(tests["passing_tests"])
    percentage = (passed / total * 100.0) if total else 0.0

    normalised = {
        "passing_tests": tests["passing_tests"],
        "failing_tests": tests["failing_tests"],
        "skipped_tests": tests["skipped_tests"],
        "xfailed_tests": tests["xfailed_tests"],
        "all_tests": tests["all_tests"],
        "warnings": warnings,
        "tests": [{"id": name, "status": "passed"} for name in tests["passing_tests"]]
        + [{"id": name, "status": "failed"} for name in tests["failing_tests"]]
        + [{"id": name, "status": "skipped"} for name in tests["skipped_tests"]]
        + [{"id": name, "status": "xfailed"} for name in tests["xfailed_tests"]]
        + [{"id": name, "status": "other"} for name in tests["other_tests"]],
    }

    output_path.write_text(
        json.dumps(normalised, indent=2, sort_keys=True), encoding="utf-8"
    )

    return {
        "total": total,
        "passed": passed,
        "failed": len(tests["failing_tests"]),
        "skipped": len(tests["skipped_tests"]),
        "xfailed": len(tests["xfailed_tests"]),
        "warnings_count": len(warnings),
        "percentage": percentage,
        "passing_items_json": json.dumps(tests["passing_tests"]),
        "failing_items_json": json.dumps(tests["failing_tests"]),
        "skipped_items_json": json.dumps(tests["skipped_tests"]),
        "xfailed_items_json": json.dumps(tests["xfailed_tests"]),
        "all_items_json": json.dumps(tests["all_tests"]),
        "warnings_json": json.dumps(warnings),
        "has_failures": "true" if tests["failing_tests"] else "false",
        "no_tests_found": "true" if total == 0 else "false",
        "collection_errors": "false",
    }


def write_outputs(summary: Dict[str, object], destination: Path) -> None:
    with destination.open("a", encoding="utf-8") as handle:
        for key, value in summary.items():
            if isinstance(value, float):
                handle.write(f"{key}={value:.2f}\n")
            else:
                handle.write(f"{key}={value}\n")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input", type=Path, help="Path to the raw Storybook results JSON file."
    )
    parser.add_argument(
        "output", type=Path, help="Destination file for the normalised JSON payload."
    )
    parser.add_argument(
        "--github-output",
        type=Path,
        default=None,
        help="Optional path to the GitHub Actions output file to append summary values.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    summary = normalise_results(args.input, args.output)

    if args.github_output:
        write_outputs(summary, args.github_output)

    print(
        json.dumps(
            {
                "total": summary["total"],
                "passed": summary["passed"],
                "failed": summary["failed"],
                "skipped": summary["skipped"],
                "xfailed": summary["xfailed"],
                "warnings": summary["warnings_count"],
                "percentage": summary["percentage"],
                "no_tests_found": summary["no_tests_found"],
            }
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
