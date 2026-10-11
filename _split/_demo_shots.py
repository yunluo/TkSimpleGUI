#!/usr/bin/env python3
"""Capture one screenshot per demo tab (for visual acceptance)."""
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import demo as demo_module  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))


def capture(window, path):
    window.tk_root.update_idletasks()
    x = window.tk_root.winfo_rootx()
    y = window.tk_root.winfo_rooty()
    width = window.tk_root.winfo_width()
    height = window.tk_root.winfo_height()
    script = os.path.join(OUT, "_shot.ps1")
    subprocess.run([
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", script, "-x", str(x), "-y", str(y),
        "-w", str(width), "-h", str(height), "-path", path,
    ], check=True)


def main():
    import PySimpleGUI4 as sg

    sg.set_dpi_awareness()  # 让 winfo 坐标与屏幕物理像素对齐，截图不漂移
    instance = demo_module.Demo()
    window = instance.build()
    window.tk_root.attributes("-topmost", True)  # 截图期间保持最前，避免被遮挡
    window.move_to_center()
    window.refresh()
    time.sleep(0.4)
    notebook = window["-TABS-"].widget
    names = ["inputs", "selection", "data", "graphics", "containers", "system"]
    for index, name in enumerate(names):
        notebook.select(index)
        window.refresh()
        time.sleep(0.25)
        capture(window, os.path.join(OUT, "_demo_tab{}.png".format(index)))
        print("captured", name, flush=True)
    window.close()
    print("ALL SHOTS DONE")


if __name__ == "__main__":
    main()
