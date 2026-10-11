# -*- coding: utf-8 -*-
"""Inventory all top-level definitions of the monolith PySimpleGUI4.py."""
import ast
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SRC = sys.argv[1] if len(sys.argv) > 1 else "PySimpleGUI4.py"

with open(SRC, "r", encoding="utf-8") as f:
    source = f.read()

tree = ast.parse(source)
lines_total = len(source.splitlines())
print("TOTAL_LINES:", lines_total)
print("GLOBALS_CALLS:", source.count("globals()"))

for node in tree.body:
    kind = type(node).__name__
    start = node.lineno
    end = node.end_lineno
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        name = node.name
        nargs = len(node.args.args)
        print("FUNC\t{}\t{}:{}\targs={}".format(name, start, end, nargs))
    elif isinstance(node, ast.ClassDef):
        print("CLASS\t{}\t{}:{}".format(node.name, start, end))
    elif isinstance(node, ast.Assign):
        names = []
        for t in node.targets:
            if isinstance(t, ast.Name):
                names.append(t.id)
            elif isinstance(t, ast.Tuple):
                names.extend(e.id for e in t.elts if isinstance(e, ast.Name))
        print("ASSIGN\t{}\t{}:{}".format(",".join(names), start, end))
    elif isinstance(node, ast.If):
        test_src = ast.get_source_segment(source, node.test) or ""
        print("IF\t{}\t{}:{}\t{}".format(test_src[:60], start, end, ""))
    elif isinstance(node, ast.Try):
        print("TRY\t\t{}:{}".format(start, end))
    elif isinstance(node, (ast.Import, ast.ImportFrom)):
        mod = getattr(node, "module", None) or ",".join(a.name for a in node.names)
        print("IMPORT\t{}\t{}:{}".format(mod, start, end))
    elif isinstance(node, ast.Expr):
        v = node.value
        if isinstance(v, ast.Constant) and isinstance(v.value, str):
            print("DOCSTRIG\t\t{}:{}".format(start, end))
        else:
            print("EXPR\t\t{}:{}".format(start, end))
    else:
        print(kind.upper() + "\t\t{}:{}".format(start, end))

# collect names in global statements inside functions
globals_used = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Global):
        globals_used.update(node.names)
print("=== GLOBAL_STMT_NAMES ({}):".format(len(globals_used)))
print(", ".join(sorted(globals_used)))
