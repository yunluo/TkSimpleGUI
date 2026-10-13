#!/usr/bin/env python3
"""Type-check gate: run ty over the package and fail on any diagnostic.

Usage: ``python tests/check_types.py`` (or wire into CI). Exits 0 when ty
reports zero errors/warnings, non-zero when ty is missing or finds issues —
a missing checker must FAIL the gate, never silently skip it.
"""
import os
import shutil
import subprocess
import sys

# explicit override wins, then PATH, then the known local install
TY_CANDIDATES = [
    os.environ.get("TY_BIN"),
    shutil.which("ty"),
    r"D:\bin\ty.exe",
]


def resolve_ty():
    for candidate in TY_CANDIDATES:
        if candidate and os.path.isfile(candidate):
            return candidate
    return None


def main():
    ty = resolve_ty()
    if ty is None:
        print(
            "FAIL: ty checker not found (set TY_BIN or put 'ty' on PATH). "
            "The type gate cannot pass without running the checker."
        )
        return 2
    # check=False is deliberate: the exit code is interpreted below, and a
    # nonzero ty result must fall through to the diagnostic printer, not raise.
    run = subprocess.run(
        [ty, "check", "src", "--python-version", "3.7"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = (run.stdout or "") + (run.stderr or "")
    if "All checks passed" in output:
        print("TYPES OK: ty reported zero diagnostics")
        return 0
    print(output)
    return 1


if __name__ == "__main__":
    sys.exit(main())
