# -*- coding: utf-8 -*-
"""Extract LOOK_AND_FEEL_TABLE from the baseline monolith into a clean data module.

The table is a pure literal (strings/tuples/ints) so ast.literal_eval is safe.
Output: src/PySimpleGUI4/_theme_data.py
"""
import ast
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SRC = "_split/baseline.py"
OUT_DIR = os.path.join("src", "PySimpleGUI4")
OUT = os.path.join(OUT_DIR, "_theme_data.py")

text = open(SRC, encoding="utf-8").read()
tree = ast.parse(text)

table_src = None
for node in tree.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == "LOOK_AND_FEEL_TABLE":
                table_src = ast.get_source_segment(text, node.value)
if table_src is None:
    print("LOOK_AND_FEEL_TABLE not found")
    sys.exit(1)

# build an evaluation namespace from the baseline's simple constant assignments
env = {}
import tkinter  # noqa: F401
import tkinter.font  # noqa: F401
from tkinter import ttk as _ttk

env["tk"] = tkinter
env["tkinter"] = tkinter
env["ttk"] = _ttk
for node in tree.body:
    if isinstance(node, ast.Assign):
        seg = ast.get_source_segment(text, node)
        if seg is None:
            continue
        try:
            exec(seg, env)
        except Exception:
            pass

table = eval(table_src, env)

lines = []
lines.append('#!/usr/bin/env python3\n')
lines.append('"""PySimpleGUI4 theme definitions.\n\nGenerated from the PySimpleGUI LOOK_AND_FEEL_TABLE by _split/gen_theme_data.py.\nPure data module - do not edit by hand.\n"""\n\n')
lines.append("LOOK_AND_FEEL_TABLE = {\n")
for name in sorted(table):
    lines.append('    "{}": {},\n'.format(name, repr(table[name])))
lines.append("}\n")

os.makedirs(OUT_DIR, exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="") as f:
    f.write("".join(lines))

print("themes:", len(table))
print("written:", OUT)
