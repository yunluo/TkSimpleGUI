#!/usr/bin/env python3
"""Parse every project .py with the running interpreter's ast (3.7 compat gate)."""
import ast
import os
import pathlib
import sys

root = pathlib.Path(os.environ.get("TKSIMPLEGUI_ROOT", os.getcwd()))
files = list((root / "src").rglob("*.py"))
files += list((root / "tests").rglob("*.py"))
demo = root / "demo.py"
if demo.exists():
    files.append(demo)

bad = []
for p in files:
    try:
        ast.parse(p.read_bytes(), filename=str(p))
    except SyntaxError as e:
        bad.append("%s:%s %s" % (p, e.lineno, e.msg))

if bad:
    print("\n".join(bad))
    sys.exit(1)
print("ALL %d FILES PARSE OK on %s" % (len(files), sys.version.split()[0]))
