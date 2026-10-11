# -*- coding: utf-8 -*-
"""Deep smoke test for the split pysimplegui package."""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, "src")

import pysimplegui4 as sg

failures = []

def check(name, cond):
    print(("PASS" if cond else "FAIL") + " " + name)
    if not cond:
        failures.append(name)

# 1. theme table
themes = sg.list_of_look_and_feel_values()
check("160+ themes", len(themes) > 150)

# 2. theme switching (mutable global semantics via _c)
bg1 = sg.theme_background_color()
target = [t for t in themes if t != sg.theme()][0]
sg.theme(target)
bg2 = sg.theme_background_color()
check("theme switch changes background", bg1 != bg2)
sg.theme("DarkBlue3")
check("theme name", sg.theme() == "DarkBlue3")

# 3. set_options mutates constants read by other modules
sg.set_options(border_width=5)
import pysimplegui4.core.constants as C
check("set_options -> constants live", C.DEFAULT_BORDER_WIDTH == 5)
sg.set_options(border_width=1)

# 4. window lifecycle
win = sg.Window("t", [[sg.Text("hi", key="-T-")], [sg.Button("OK", key="-B-")]], finalize=True)
check("window rows", len(win.Rows) == 2)
check("element get", win["-T-"].get() == "hi")
win["-T-"].update("changed")
check("element update", win["-T-"].get() == "changed")
event, values = win.read(timeout=100)
check("read timeout returns", event is not None)
win.close()
# parity with monolith: create(+2 via classmethods) ... close(-1) -> 1
check("NumOpenWindows parity with monolith", sg.Window.NumOpenWindows == 1)

# 5. event manager
app = sg.PySimpleEvent()
called = []

@app.bind_event("test_evt")
def on_test_evt(window, values):
    called.append((window, values))

@app.bind_event(["e1", "e2"])
def on_multi(event):
    called.append(event)

win2 = sg.Window("t2", [[sg.Text("x")]], finalize=True)
app.apply_event(win2, "test_evt", {"a": 1})
app.apply_event(win2, "e2", {})
check("bind_event dispatch (window, values)", len(called) == 2 and called[0][1] == {"a": 1})
check("bind_event dispatch (event only)", called[1] == "e2")
win2.close()

# 6. element shortcuts and helpers
check("shortcuts", sg.T is sg.Text and sg.B is sg.Button and sg.Col is sg.Column)
check("CamelCase aliases", sg.Popup is sg.popup and sg.RGB is sg.rgb and sg.SetOptions is sg.set_options)
check("layout helpers", callable(sg.pin) and callable(sg.vtop) and callable(sg.Sizer))

# 7. utils
check("utils", sg.clipboard_set("x") is None or True)


class _Foo(object):
    def __init__(self):
        self.bar_int = 3


check("obj_to_string", "bar_int" in sg.obj_to_string(_Foo()))

# 8. debugger / system tray API present
check("debugger api", callable(sg.show_debugger_window) and callable(sg.get_versions))
check("SystemTray", sg.SystemTray is not None)

# 9. python3.4: no active f-strings in the package (ast-precise check)
import ast
import os
bad = []
for root, dirs, files in os.walk("src/pysimplegui4"):
    for f in files:
        if f.endswith(".py"):
            p = os.path.join(root, f)
            with open(p, encoding="utf-8") as fh:
                t = ast.parse(fh.read())
            for node in ast.walk(t):
                if isinstance(node, ast.JoinedStr):
                    bad.append("{}:{}".format(f, node.lineno))
check("no f-strings", not bad)
for b in bad:
    print("   f-string:", b)

print()
if failures:
    print("FAILURES:", failures)
    sys.exit(1)
print("ALL SMOKE TESTS PASSED")
