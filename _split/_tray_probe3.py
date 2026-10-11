#!/usr/bin/env python3
"""Heavier repro: many ttk-rich windows, then tray."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import PySimpleGUI4 as sg

print("step: windows", flush=True)
for i in range(12):
    w = sg.Window(
        "t",
        [
            [sg.Text("x"), sg.Input("", key="-I-"), sg.Button("b", key="-B-")],
            [sg.Table([["a"], ["b"]], headings=["H"], key="-TB-"),
             sg.Checkbox("c"), sg.Combo(["a"])],
            [sg.CheckList(["p", "q"]), sg.Toolbar(["t1", "t2"])],
        ],
        finalize=True,
    )
    w.read(timeout=30)
    w.close()
print("step: tray create", flush=True)
tray = sg.SystemTray(title="probe3", menu=["One", "Two"])
print("step: tray read", flush=True)
event, _ = tray.read(timeout=100)
print("step: tray read ->", event, flush=True)
tray.close()
print("SURVIVED", flush=True)
