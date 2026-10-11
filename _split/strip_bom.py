# -*- coding: utf-8 -*-
"""Strip UTF-8 BOMs from package source files."""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

count = 0
for root, dirs, files in os.walk("src/PySimpleGUI4"):
    for name in files:
        if not name.endswith(".py"):
            continue
        path = os.path.join(root, name)
        raw = open(path, "rb").read()
        if raw.startswith(b"\xef\xbb\xbf"):
            open(path, "wb").write(raw[3:])
            print("BOM stripped:", path)
            count += 1
print("stripped:", count)
