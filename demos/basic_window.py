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

UI strings are Chinese (menu/button labels double as event names).
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
        "任务清单",
        [
            [ts.Text("实时按键事件："),
             ts.Input(key="lot1", size=(24, 1), enable_events=True)],
            [ts.Text("按回车触发事件："),
             ts.Input(key="lot2", size=(24, 1))],
            [ts.Button("关于"), ts.Button("保存配置")],
            [ts.Text("实时：", size=(6, 1)), ts.Text("", key="lot3", size=(40, 1))],
            [ts.Text("回车：", size=(6, 1)), ts.Text("", key="lot4", size=(40, 1))],
        ],
        size=(440, 200),
    )
    return ts.Window(
        "TkSimpleGUI 基础窗口",
        [[task_list], [ts.StatusBar("就绪", key="-STATUS-", expand_x=True)]],
        resizable=True,
        finalize=True,
    )


@app.bind_event("lot1")
def on_lot1(window, values):
    window["lot3"].update(values.get("lot1", ""))


@app.bind_event("lot2")
def on_lot2(window, values):
    window["lot4"].update("你输入了：" + str(values.get("lot2", "")))


@app.bind_event("关于")
def on_about(window, values):
    ts.popup(
        "TkSimpleGUI " + ts.__version__,
        "推荐写法：bind_event + Window.run()",
        title="关于",
    )
    window["-STATUS-"].update("已显示关于")


@app.bind_event("保存配置")
def on_save_config(window, values):
    ts.popup("配置已保存（仅演示）")
    window["-STATUS-"].update("配置已保存")


def main():
    window = make_main_window()
    # the on_close hook intercepts the title bar X; the popup gives the
    # user a chance to cancel an accidental click
    window.on_close = lambda w: ts.popup_yes_no(
        "确定关闭基础窗口演示吗？", title="退出") == "Yes"
    try:
        app.run_event(window)
    finally:
        window.close()


if __name__ == "__main__":
    main()
