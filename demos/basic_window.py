#!/usr/bin/env python3
"""Basic TkSimpleGUI window -- the recommended starting template.

Run::

    python demos/basic_window.py

Demonstrates the framework defaults:

* a single ``Window.run()`` call replaces the user event loop
* ``@ts.bind_event`` handlers dispatch by element key (no manual
  ``if event == ...:`` chains)
* popups are closable from the title bar X; the OK / Cancel buttons are
  one of the many ways to answer
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import TkSimpleGUI as ts

ts.theme("System")

app = ts.default_app()


def make_main_window():
    """A focused, beginner-friendly layout (no menus, no tabs, no toolbars)."""
    task_list = ts.Frame(
        "Tasks",
        [
            [ts.Text("Live keystroke events:"),
             ts.Input(key="lot1", size=(24, 1), enable_events=True)],
            [ts.Text("Press Enter to fire an event:"),
             ts.Input(key="lot2", size=(24, 1))],
            [ts.Button("About"), ts.Button("Save config")],
            [ts.Text("Live:", size=(6, 1)), ts.Text("", key="lot3", size=(40, 1))],
            [ts.Text("Enter:", size=(6, 1)), ts.Text("", key="lot4", size=(40, 1))],
        ],
        size=(440, 200),
    )
    return ts.Window(
        "Basic TkSimpleGUI window",
        [[task_list], [ts.StatusBar("ready", key="-STATUS-", expand_x=True)]],
        resizable=True,
        finalize=True,
    )


@app.bind_event("lot1")
def on_lot1(window, values):
    window["lot3"].update(values.get("lot1", ""))


@app.bind_event("lot2")
def on_lot2(window, values):
    window["lot4"].update("you typed: " + str(values.get("lot2", "")))


@app.bind_event("About")
def on_about(window, values):
    ts.popup(
        "TkSimpleGUI " + ts.__version__,
        "Recommended pattern: bind_event + Window.run()",
        title="About",
    )
    window["-STATUS-"].update("about shown")


@app.bind_event("Save config")
def on_save_config(window, values):
    ts.popup("config saved (demo only)")
    window["-STATUS-"].update("config saved")


def main():
    window = make_main_window()
    # the on_close hook intercepts the title bar X; the popup gives the
    # user a chance to cancel an accidental click
    window.on_close = lambda w: ts.popup_yes_no(
        "Close the basic window demo?", title="Exit") == "Yes"
    try:
        app.run_event(window)
    finally:
        window.close()


if __name__ == "__main__":
    main()
