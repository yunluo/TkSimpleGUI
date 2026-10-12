#!/usr/bin/env python3
"""Syntax gate: parse every project .py with the RUNNING interpreter's ast.

The value of this gate depends on the interpreter that runs it: executed
under 3.7 it proves 3.7 parseability (the project floor); under newer
interpreters it only catches generic syntax errors. CI therefore runs it
on both 3.7 and the newest Python (see .github/workflows).
"""
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
print(
    "ALL %d FILES PARSE OK on %s%s"
    % (len(files), sys.version.split()[0],
       " (project floor - authoritative)" if sys.version_info[:2] == (3, 7) else "")
)
