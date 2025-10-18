#!/usr/bin/env python3
"""Convert a .trx test report into a pytest-json-report compatible structure."""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List

NS = {"ns": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}


def _safe_int(value: str | None) -> int:
    try:
        return int(value) if value is not None else 0
    except ValueError:
        return 0


def _collect_test_metadata(root: ET.Element) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for unit_test in root.findall(".//ns:UnitTest", NS):
        test_id = unit_test.get("id") or unit_test.get("Id")
        if not test_id:
            continue
        name = unit_test.get("name") or unit_test.get("Name")
        method = unit_test.find("ns:TestMethod", NS)
        class_name = method.get("className") if method is not None else None
        method_name = method.get("name") if method is not None else None
        storage = unit_test.get("storage") or unit_test.get("Storage")

        parts: List[str] = []
        if storage:
            parts.append(Path(storage).stem)
        if class_name:
            parts.append(class_name)
        if method_name:
            parts.append(method_name)
        elif name:
            parts.append(name)

        if parts:
            mapping[test_id] = "::".join(parts)
        elif name:
            mapping[test_id] = name
        else:
            mapping[test_id] = test_id
    return mapping


def _build_test_entry(
    result: ET.Element, id_to_name: Dict[str, str]
) -> Dict[str, object]:
    test_id = result.get("testId") or result.get("testID") or ""
    display_name = id_to_name.get(
        test_id, result.get("testName") or test_id or "unknown"
    )
    outcome = (result.get("outcome") or "unknown").lower()

    if outcome == "notexecuted" or outcome == "inconclusive":
        outcome_label = "skipped"
    elif outcome == "passed":
        outcome_label = "passed"
    elif outcome == "failed":
        outcome_label = "failed"
    else:
        outcome_label = outcome or "unknown"

    longrepr: List[str] = []
    output = result.find("ns:Output", NS)
    if output is not None:
        error_info = output.find("ns:ErrorInfo", NS)
        if error_info is not None:
            message = error_info.findtext("ns:Message", default="", namespaces=NS)
            stack = error_info.findtext("ns:StackTrace", default="", namespaces=NS)
            if message:
                longrepr.append(message.strip())
            if stack:
                longrepr.append(stack.strip())

    return {
        "nodeid": display_name,
        "outcome": outcome_label,
        "longrepr": longrepr,
    }


def _default_report() -> Dict[str, object]:
    return {
        "summary": {"total": 0, "passed": 0, "failed": 0, "skipped": 0},
        "tests": [],
        "exitcode": 0,
    }


def convert_trx(trx_path: Path) -> Dict[str, object]:
    if not trx_path.exists():
        return _default_report()

    try:
        tree = ET.parse(trx_path)
    except ET.ParseError:
        return _default_report()

    root = tree.getroot()
    summary = root.find("ns:ResultSummary", NS)
    counters = summary.find("ns:Counters", NS) if summary is not None else None

    total = _safe_int(counters.get("total")) if counters is not None else 0
    passed = _safe_int(counters.get("passed")) if counters is not None else 0
    failed = _safe_int(counters.get("failed")) if counters is not None else 0
    skipped = _safe_int(counters.get("notExecuted")) if counters is not None else 0

    id_to_name = _collect_test_metadata(root)
    tests = [
        _build_test_entry(result, id_to_name)
        for result in root.findall(".//ns:UnitTestResult", NS)
    ]

    exitcode = 0 if failed == 0 else 1

    return {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
        },
        "tests": tests,
        "exitcode": exitcode,
    }


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: trx_to_pytest_json.py <input.trx> <output.json>", file=sys.stderr)
        return 2

    trx_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    report = convert_trx(trx_path)

    output_path.write_text(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
