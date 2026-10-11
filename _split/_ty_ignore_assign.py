#!/usr/bin/env python3
"""Append `# ty: ignore[invalid-assignment]` to None-initializations of
attributes that are declared non-Optional (they are always set again in
_create_widget before any accessor runs)."""
import io

LINES = {
    "src/PySimpleGUI4/window/window.py": [132, 159, 943],
    "src/PySimpleGUI4/elements/widgets.py": [222, 360, 586, 678, 959],
    "src/PySimpleGUI4/window/system_tray.py": [107, 333],
    "src/PySimpleGUI4/elements/containers.py": [510, 511],
    "src/PySimpleGUI4/elements/misc.py": [151],
    "src/PySimpleGUI4/elements/calendar.py": [78, 79],
}
MARK = "  # ty: ignore[invalid-assignment]"
for path, linenos in LINES.items():
    lines = io.open(path, encoding="utf-8").read().splitlines()
    for lineno in linenos:
        index = lineno - 1
        if lines[index].rstrip().endswith(MARK.strip()):
            continue
        lines[index] = lines[index].rstrip() + MARK
    io.open(path, "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")
    print("done", path)
