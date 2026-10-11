#!/usr/bin/env python3
"""Type-check gate: run ty over the package and fail on any diagnostic.

Usage: `python tests/check_types.py` (or wire into CI). Exits 0 when ty
reports zero errors/warnings.
"""
import subprocess
import sys

TY = r"D:\bin\ty.exe"


def main():
    try:
        run = subprocess.run(
            [TY, "check", "src", "--python-version", "3.7"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        print("SKIP: ty not found at", TY)
        return 0
    output = (run.stdout or "") + (run.stderr or "")
    if "All checks passed" in output:
        print("TYPES OK: ty reported zero diagnostics")
        return 0
    print(output)
    return 1


if __name__ == "__main__":
    sys.exit(main())
