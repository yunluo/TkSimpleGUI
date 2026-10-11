# -*- coding: utf-8 -*-
"""One-off: rename package references pysimplegui -> pysimplegui4 in demo/tests."""
FILES = [
    "tests/test_basic.py",
    "tests/test_all_features.py",
    "tests/test_functions.py",
    "demo.py",
]
for f in FILES:
    text = open(f, encoding="utf-8").read()
    new = text.replace("pysimplegui", "pysimplegui4")
    if new != text:
        open(f, "w", encoding="utf-8", newline="").write(new)
        print("updated:", f)
    else:
        print("unchanged:", f)
