#!/usr/bin/env python3
"""Strip the Python 3.4-era typing try/except guards (floor is now 3.7)."""
import io
import re

PATTERN = re.compile(
    r"try:\n    from typing import ([^\n]+)\nexcept ImportError:\n    [^\n]*= None\n"
)

TARGETS = [
    "src/PySimpleGUI4/__init__.py",
    "src/PySimpleGUI4/_theming.py",
    "src/PySimpleGUI4/actions.py",
    "src/PySimpleGUI4/event.py",
    "src/PySimpleGUI4/i18n.py",
    "src/PySimpleGUI4/popup.py",
    "src/PySimpleGUI4/settings.py",
    "src/PySimpleGUI4/user_settings.py",
    "src/PySimpleGUI4/utils.py",
    "src/PySimpleGUI4/window/window.py",
    "src/PySimpleGUI4/window/system_tray.py",
    "src/PySimpleGUI4/animation.py",
    "src/PySimpleGUI4/elements/base.py",
    "src/PySimpleGUI4/elements/buttons.py",
    "src/PySimpleGUI4/elements/calendar.py",
    "src/PySimpleGUI4/elements/containers.py",
    "src/PySimpleGUI4/elements/data.py",
    "src/PySimpleGUI4/elements/media.py",
    "src/PySimpleGUI4/elements/misc.py",
    "src/PySimpleGUI4/elements/widgets.py",
]


def main():
    changed = 0
    for path in TARGETS:
        source = io.open(path, encoding="utf-8").read()
        match = PATTERN.search(source)
        if match is None:
            print("no guard:", path)
            continue
        source = PATTERN.sub(lambda m: "from typing import " + m.group(1) + "\n", source)
        io.open(path, "w", encoding="utf-8", newline="").write(source)
        changed += 1
        print("stripped:", path)
    print("changed:", changed)


if __name__ == "__main__":
    main()
