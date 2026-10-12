#!/usr/bin/env python3
"""Tray run probe with step tracing (writes to a file, flushes each step)."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
import TkSimpleGUI as sg

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tray_run_trace.txt")


def trace(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


if os.path.exists(LOG):
    os.remove(LOG)

trace("start")
app = sg.TkSimpleEvent()
tray = sg.SystemTray(title="tray run probe", menu=["Exit"])
trace("tray created")


@app.bind_event("Exit")
def on_exit(window, values):
    # the framework injects the event owner (the tray) as "window"
    trace(f"handler: Exit received (owner={type(window).__name__})")
    window.close()


def fake_exit():
    trace("after fired: posting Exit")
    tray._events.put("Exit")


tray._ensure_pump_root()
tray._tk_root.after(200, fake_exit)
trace("entering tray.run()")
tray.run(app)
trace("run returned")
print("TRAY RUN OK", flush=True)
# the tray's Win32 message window can AV during interpreter finalization
# (SEH-visible, documented); exit hard to keep the probe deterministic
os._exit(0)
