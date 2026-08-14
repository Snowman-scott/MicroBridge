#!/usr/bin/env python3
import sys
from pathlib import Path

import pytest


class _Reporter:
    def __init__(self):
        self.files = {}

    def pytest_runtest_logreport(self, report):
        if report.when != "call":
            return
        fname = Path(report.nodeid.split("::")[0]).name
        entry = self.files.setdefault(fname, {"passed": 0, "failed": 0, "skipped": 0, "total": 0})
        entry["total"] += 1
        if report.skipped:
            entry["skipped"] += 1
        elif report.failed:
            entry["failed"] += 1
        else:
            entry["passed"] += 1


def main():
    test_dir = Path(__file__).parent / "tests"
    reporter = _Reporter()
    exit_code = pytest.main([str(test_dir), "-v", "--tb=short"], plugins=[reporter])

    # ── Summary table ────────────────────────────────────
    results = []
    all_passed = 0
    all_failed = 0
    all_total = 0

    for f in sorted(test_dir.glob("test_*.py")):
        entry = reporter.files.get(f.name, {"passed": 0, "failed": 0, "skipped": 0, "total": 0})
        results.append({
            "file": f.name,
            "total": entry["total"],
            "passed": entry["passed"],
            "failed": entry["failed"],
            "ok": entry["failed"] == 0 and entry["total"] > 0,
            "empty": entry["total"] == 0,
        })
        all_total += entry["total"]
        all_passed += entry["passed"]
        all_failed += entry["failed"]

    def cell(text, w):
        return (" " + text).ljust(w)

    W = 35
    print()
    print("  " + "╔" + "═" * W + "╦" + "═" * 8 + "╦" + "═" * 8 + "╗")
    print("  " + "║" + cell("Test file", W) + "║" + cell("Count", 8) + "║" + cell("Status", 8) + "║")
    print("  " + "╠" + "═" * W + "╬" + "═" * 8 + "╬" + "═" * 8 + "╣")
    for r in results:
        label = r["file"].replace(".py", "")
        if r["empty"]:
            icon = " ○"
        else:
            icon = " ✅" if r["ok"] else " ❌"
        count = f"{r['passed']}/{r['total']}"
        print(f"  ║{cell(label, W)}║{cell(count, 8)}║{cell(icon, 8)}║")
    print("  " + "╠" + "═" * W + "╬" + "═" * 8 + "╬" + "═" * 8 + "╣")
    icon = " ✅" if all_failed == 0 and all_total > 0 else " ❌"
    count = f"{all_passed}/{all_total}"
    print(f"  ║{cell('Total', W)}║{cell(count, 8)}║{cell(icon, 8)}║")
    print("  " + "╚" + "═" * W + "╩" + "═" * 8 + "╩" + "═" * 8 + "╝")
    print()

    sys.exit(1 if all_failed > 0 else exit_code)


if __name__ == "__main__":
    main()
