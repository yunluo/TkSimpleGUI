#!/usr/bin/env python3
"""Reproduce the suite-context tray crash: windows first, then tray."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import PySimpleGUI4 as sg

print("step: windows", flush=True)
for i in range(3):
    w = sg.Window("t", [[sg.Text("x")], [sg.Button("b")]], finalize=True)
    w.read(timeout=50)
    w.close()
print("step: tray create", flush=True)
tray = sg.SystemTray(title="probe2", menu=["One", "Two"])
print("step: tray read", flush=True)
event, _ = tray.read(timeout=100)
print("step: tray read ->", event, flush=True)
tray.close()
print("SURVIVED", flush=True)
