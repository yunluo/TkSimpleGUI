#!/usr/bin/env python3
"""Probe canvas button click synthesis."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import PySimpleGUI4 as sg

button = sg.RoundButton("Go", size=(90, 30), radius=14, fill_color="#e91e63", key="-RB-")
w = sg.Window("t", [[button]], finalize=True)
w.tk_root.update()
w.tk_root.deiconify()
w.tk_root.update()

hits = button.widget.find_overlapping(45, 15, 45, 15)
print("background id:", button._background_id, "overlapping:", hits)

button.widget.event_generate("<Button-1>", x=45, y=15)
w.tk_root.update()
import time
deadline = time.time() + 1.0
event = sg.TIMEOUT_KEY
while time.time() < deadline:
    event, _ = w.read(timeout=50)
    if event != sg.TIMEOUT_KEY:
        break
print("event:", event)
w.close()
