#!/usr/bin/env python3
"""Minimal SystemTray smoke probe: create, pump, close. Flush at each step."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import PySimpleGUI4 as sg

print("step: create", flush=True)
tray = sg.SystemTray(title="probe", menu=["One", "Two"])
print("step: created hwnd=%r" % tray._hwnd, flush=True)
event, _ = tray.read(timeout=100)
print("step: read ->", event, flush=True)
tray.ShowMessage("Hi", "Body")
print("step: notified", flush=True)
tray.close()
print("step: closed", flush=True)
print("SURVIVED", flush=True)
