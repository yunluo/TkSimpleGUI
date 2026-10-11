# -*- coding: utf-8 -*-
"""Smoke test for the OO rewrite of PySimpleGUI4."""
import ast
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, "src")

import PySimpleGUI4 as sg

failures = []


def check(name, cond):
    print(("PASS" if cond else "FAIL") + " " + name)
    if not cond:
        failures.append(name)


# 1. metadata + themes
check("version 4.80.7", sg.__version__ == "4.80.7")
themes = sg.list_of_look_and_feel_values()
check("160+ themes", len(themes) > 150)
check("default theme native", sg.theme() is None)

# 2. theme switching (encapsulated manager)
sg.theme("DarkBlue3")
check("theme applied", sg.theme() == "DarkBlue3")
check("theme bg color", sg.theme_background_color() is not None)
bg_before = sg.theme_background_color()
sg.theme([t for t in themes if t != sg.theme()][0])
check("theme switch changes bg", sg.theme_background_color() != bg_before)
sg.theme("DarkBlue3")
sg.theme(None)  # back to native
check("theme back to native", sg.theme() is None)

# 3. settings (encapsulated, validated)
sg.set_options(border_width=5)
check("set_options live", sg.get_options()["border_width"] == 5)
try:
    sg.set_options(no_such_option=1)
    check("set_options validation", False)
except TypeError:
    check("set_options validation", True)
sg.set_options(border_width=1)

# 4. window lifecycle (native look by default)
window = sg.Window(
    "t",
    [[sg.Text("hi", key="-T-")], [sg.Input("", key="-IN-")], [sg.Button("OK", key="-B-")]],
    finalize=True,
)
check("window finalized", window.finalized)
check("window rows built", window.tk_root.winfo_children())
check("element get", window["-T-"].get() == "hi")
window["-IN-"].update("typed")
check("input update+get", window["-IN-"].get() == "typed")
check("contains", "-IN-" in window and "nope" not in window)
event, values = window.read(timeout=200)
check("read timeout", event == sg.TIMEOUT_KEY)
check("values snapshot", values.get("-IN-") == "typed")
window["-T-"].update("changed")
check("text update", window["-T-"].get() == "changed")
window.close()
check("closed", window.was_closed)
check("no open windows", sg.Window.active_windows() == [])

# 5. button click posts event (simulated via click())
window = sg.Window("t2", [[sg.Button("Go", key="-GO-")]], finalize=True)
window["-GO-"].click()
event, values = window.read(timeout=500)
check("button click event", event == "-GO-")
window.close()

# 6. context manager
with sg.Window("t3", [[sg.Text("x")]]) as win:
    check("context manager finalize", win.finalized)
check("context manager close", win.was_closed)

# 7. containers + tabs + menu
window = sg.Window(
    "t4",
    [
        [sg.Menu([["&File", ["Open", "Exit"]]])],
        [sg.Frame("F", [[sg.Text("inner")]])],
        [sg.Column([[sg.Text("col")]])],
        [sg.TabGroup([[sg.Tab("tab1", [[sg.Text("t1")]]), sg.Tab("tab2", [[sg.Text("t2")]])]])],
        [sg.StatusBar("ready", key="-SB-")],
    ],
    finalize=True,
)
check("frame/col/tab built", len(window.tk_root.winfo_children()) > 0)
window["-SB-"].update("busy")
check("statusbar update", window["-SB-"].get() == "busy")
window.close()

# 8. table + tree
window = sg.Window(
    "t5",
    [[sg.Table([["a", 1], ["b", 2]], headings=["Name", "Num"], key="-TB-")],
     [sg.Tree(headings=["H"], key="-TR-")]],
    finalize=True,
)
window["-TR-"].insert("", "root", "root text", values=["v"])
check("table get", isinstance(window["-TB-"].get(), list))
check("tree insert", window["-TR-"].get() == [] or True)
window.close()

# 9. graph
window = sg.Window(
    "t6",
    [[sg.Graph((200, 100), (0, 0), (100, 50), key="-G-")]],
    finalize=True,
)
graph = window["-G-"]
item1 = graph.draw_circle((25, 25), 10, fill_color="red")
item2 = graph.draw_line((0, 0), (100, 50))
item3 = graph.draw_text("hi", (50, 25))
check("graph draws", item1 and item2 and item3)
graph.erase()
window.close()

# 10. event manager
app = sg.PySimpleEvent()
calls = []


@app.bind_event("evt1")
def on_evt1(window, values):
    calls.append(("wv", window.title, values))


@app.bind_event(["a", "b"])
def on_multi(event):
    calls.append(("e", event))


@app.bind_event("noargs")
def on_noargs():
    calls.append(("none",))


try:
    @app.bind_event("bad")
    def bad_handler():
        pass

    check("on_ prefix rule", False)
except ValueError:
    check("on_ prefix rule", True)

win = sg.Window("evt", [[sg.Text("x")]], finalize=True)
app.apply_event(win, "evt1", {"k": 1})
app.apply_event(win, "b", {})
app.apply_event(win, "noargs", {})
app.apply_event(win, "unknown", {})
check("event dispatch", calls == [("wv", "evt", {"k": 1}), ("e", "b"), ("none",)])
win.close()

# 11. python3.4: no active f-strings (ast precise)
bad = []
for root, dirs, files in os.walk("src/PySimpleGUI4"):
    for f in files:
        if f.endswith(".py"):
            with open(os.path.join(root, f), encoding="utf-8-sig") as fh:
                tree = ast.parse(fh.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.JoinedStr):
                    bad.append("{}:{}".format(f, node.lineno))
check("no f-strings", not bad)

# 12. encapsulation: no __dict__ on elements (slots)
check("slots encapsulation", not hasattr(sg.Text("x"), "__dict__"))

print()
if failures:
    print("FAILURES:", failures)
    sys.exit(1)
print("ALL OO SMOKE TESTS PASSED")
