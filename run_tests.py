#!/usr/bin/env python3
import contextlib
import importlib.util
import io
import sys
import unittest
from pathlib import Path


def _load_and_run_tests(path, verbosity=2):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(mod)

    buf = io.StringIO()
    runner = unittest.TextTestRunner(stream=buf, verbosity=verbosity)
    with contextlib.redirect_stdout(io.StringIO()):
        with contextlib.redirect_stderr(io.StringIO()):
            result = runner.run(suite)

    return result, buf.getvalue()


def main():
    test_dir = Path(__file__).parent / "tests"
    files = sorted(test_dir.glob("test_*.py"))

    results = []
    all_passed = 0
    all_failed = 0
    all_total = 0

    for f in files:
        result, output = _load_and_run_tests(f)
        total = result.testsRun
        failed = len(result.failures) + len(result.errors)
        passed = total - failed

        results.append({
            "file": f.name,
            "total": total,
            "passed": passed,
            "failed": failed,
            "ok": failed == 0,
        })
        all_total += total
        all_passed += passed
        all_failed += failed

        print(output, end="")

    # ── Summary table ────────────────────────────────────

    def cell(text, w):
        return (" " + text).ljust(w)

    W = 35
    print()
    print("  " + "╔" + "═" * W + "╦" + "═" * 8 + "╦" + "═" * 8 + "╗")
    print("  " + "║" + cell("Test file", W) + "║" + cell("Count", 8) + "║" + cell("Status", 8) + "║")
    print("  " + "╠" + "═" * W + "╬" + "═" * 8 + "╬" + "═" * 8 + "╣")
    for r in results:
        label = r["file"].replace(".py", "")
        icon = " ✅" if r["ok"] else " ❌"
        count = f"{r['passed']}/{r['total']}"
        print(f"  ║{cell(label, W)}║{cell(count, 8)}║{cell(icon, 8)}║")
    print("  " + "╠" + "═" * W + "╬" + "═" * 8 + "╬" + "═" * 8 + "╣")
    icon = " ✅" if all_failed == 0 else " ❌"
    count = f"{all_passed}/{all_total}"
    print(f"  ║{cell('Total', W)}║{cell(count, 8)}║{cell(icon, 8)}║")
    print("  " + "╚" + "═" * W + "╩" + "═" * 8 + "╩" + "═" * 8 + "╝")
    print()

    sys.exit(1 if all_failed > 0 else 0)


if __name__ == "__main__":
    main()
