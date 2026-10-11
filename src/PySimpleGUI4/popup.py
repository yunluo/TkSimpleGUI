#!/usr/bin/env python3
"""Popup dialogs for PySimpleGUI4.

Every popup is built from :class:`~PySimpleGUI4.window.Window` itself, so
popups automatically follow the active theme.
"""

import time

from . import constants as C
from . import settings as settings_mod
from .elements.buttons import Button
from .elements.widgets import Input, Multiline, Text
from .window.window import Window

try:
    from typing import Any, List, Optional, Tuple
except ImportError:
    Any = List = Optional = Tuple = None


def _popup_window(
    title,
    lines,
    buttons=("OK",),
    auto_close_duration=None,
    no_buttons=False,
    size=(None, None),
):
    """Shared helper: build and read a simple popup window."""
    rows = [[Text(line)] for line in lines]
    if not no_buttons and buttons:
        rows.append([Button(label, key=label) for label in buttons])
    window = Window(title, rows, size=size, finalize=True)
    if no_buttons:
        duration = (
            auto_close_duration
            if auto_close_duration is not None
            else settings_mod.settings.autoclose_time
        )
        window.read(timeout=int(duration * 1000), close=True)
        return ""
    event, _values = window.read(close=True)
    return event


def _message_lines(args):
    lines = []
    for arg in args:
        text = str(arg)
        lines.extend(text.split("\n"))
    return lines or [""]


def popup(*args, title="", button_color=None, auto_close=False, auto_close_duration=None):
    """Show a message with an OK button; returns the clicked button text."""
    if auto_close:
        return popup_auto_close(
            *args, title=title, auto_close_duration=auto_close_duration
        )
    return _popup_window(title, _message_lines(args))


def popup_ok(*args, title=""):
    """Show a message with an OK button; returns ``"OK"``."""
    return _popup_window(title, _message_lines(args), buttons=("OK",))


def popup_yes_no(*args, title=""):
    """Show a message with Yes/No buttons; returns ``"Yes"`` or ``"No"``."""
    return _popup_window(title, _message_lines(args), buttons=("Yes", "No"))


def popup_ok_cancel(*args, title=""):
    """Show a message with OK/Cancel buttons; returns the clicked one."""
    return _popup_window(title, _message_lines(args), buttons=("OK", "Cancel"))


def popup_cancel(*args, title=""):
    """Show a message with a Cancel button; returns ``"Cancel"``."""
    return _popup_window(title, _message_lines(args), buttons=("Cancel",))


def popup_error(*args, title="Error"):
    """Show an error message; returns ``"OK"``."""
    return _popup_window(title, _message_lines(args), buttons=("OK",))


def popup_error_with_traceback(*args, **kwargs):
    """Show an error message (traceback helpers are not available)."""
    return popup_error(*args, title=kwargs.get("title", "Error"))


def popup_no_buttons(*args, title="", non_blocking=True, auto_close_duration=None):
    """Show a message without buttons; auto closes. Returns ``""``."""
    return _popup_window(
        title,
        _message_lines(args),
        buttons=(),
        no_buttons=True,
        auto_close_duration=auto_close_duration,
    )


def popup_non_blocking(*args, title="", auto_close_duration=None):
    """Show a message and return immediately (auto closes)."""
    return popup_no_buttons(
        *args, title=title, auto_close_duration=auto_close_duration
    )


def popup_quick(*args, title="", auto_close_duration=None):
    """Alias of :func:`popup_non_blocking`."""
    return popup_non_blocking(*args, title=title, auto_close_duration=auto_close_duration)


def popup_quick_message(*args, title="", auto_close_duration=None):
    """Alias of :func:`popup_non_blocking`."""
    return popup_non_blocking(*args, title=title, auto_close_duration=auto_close_duration)


def popup_auto_close(*args, title="", auto_close_duration=None, buttons=("OK",)):
    """Show a message with buttons that closes itself after a delay."""
    duration = (
        auto_close_duration
        if auto_close_duration is not None
        else settings_mod.settings.autoclose_time
    )
    lines = _message_lines(args)
    rows = [[Text(line)] for line in lines]
    rows.append([Button(label, key=label) for label in buttons])
    window = Window(title, rows, finalize=True)
    event, _values = window.read(timeout=int(duration * 1000), close=True)
    if event == C.TIMEOUT_KEY:
        return buttons[0] if buttons else ""
    return event


def popup_timed(*args, title="", auto_close_duration=None):
    """Alias of :func:`popup_auto_close`."""
    return popup_auto_close(*args, title=title, auto_close_duration=auto_close_duration)


def popup_annoying(*args, title=""):
    """Show a message repeatedly until the user answers; returns the answer."""
    while True:
        result = _popup_window(title, _message_lines(args), buttons=("OK",))
        if result:
            return result


def popup_no_titlebar(*args, title="", **kwargs):
    """Show a borderless message popup; returns the clicked button text."""
    return _popup_window("", _message_lines(args))


def popup_scrolled(*args, title="", size=(80, 20)):
    """Show a scrollable message; returns the text (or None on cancel)."""
    rows = [[Multiline("\n".join(_message_lines(args)), size=size, key="-ML-")]]
    rows.append([Button("OK", key="OK"), Button("Cancel", key="Cancel")])
    window = Window(title, rows, finalize=True)
    window["-ML-"].widget.configure(state="disabled")
    event, _values = window.read(close=True)
    if event == "Cancel":
        return None
    return "\n".join(_message_lines(args))


def popup_notify(*args, title="Notification"):
    """Show a short auto closing notification."""
    return popup_no_buttons(*args, title=title, auto_close_duration=3)


def popup_get_text(message, title="", default_text=""):
    """Ask the user for a single line of text; None on cancel."""
    rows = [
        [Text(message)],
        [Input(default_text, key="-IN-", size=(50, 1))],
        [Button("OK", key="OK"), Button("Cancel", key="Cancel")],
    ]
    window = Window(title, rows, finalize=True)
    window["-IN-"].widget.bind("<Return>", lambda _e: window._post_event("OK"))
    window["-IN-"].widget.focus_set()
    event, values = window.read(close=True)
    if event == "OK":
        return values.get("-IN-", "")
    return None


def popup_get_file(
    message="",
    title="",
    file_types=C.FILE_TYPES_ALL_FILES,
    save_as=False,
    multiple_files=False,
    initial_folder=None,
    default_path=None,
):
    """Native file picker; returns a path (or delimiter joined paths) or None."""
    from tkinter import filedialog

    options = {
        "title": title or message,
        "filetypes": tuple(file_types),
    }
    if initial_folder:
        options["initialdir"] = initial_folder
    if default_path:
        options["initialfile"] = default_path
    if save_as:
        result = filedialog.asksaveasfilename(**options)
    elif multiple_files:
        chosen = filedialog.askopenfilenames(**options)
        result = C.BROWSE_FILES_DELIMITER.join(chosen) if chosen else None
    else:
        result = filedialog.askopenfilename(**options)
    return result if result else None


def popup_get_folder(message="", title=""):
    """Native folder picker; returns the path or None."""
    from tkinter import filedialog

    result = filedialog.askdirectory(title=title or message)
    return result if result else None


def popup_get_date(message="Choose a date", title=""):
    """Native calendar chooser; returns (year, month, day) or None."""
    import calendar
    import tkinter as tk
    from tkinter import ttk

    now = time.localtime()
    year, month = now.tm_year, now.tm_mon
    result = {"date": None}

    def _draw():
        cal_frame.configure(text="{} {}".format(calendar.month_name[month], year))
        for child in grid_frame.winfo_children():
            child.destroy()
        days = calendar.monthcalendar(year, month)
        for col, day_name in enumerate(("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")):
            ttk.Label(grid_frame, text=day_name).grid(row=0, column=col)
        for row_index, week in enumerate(days, start=1):
            for col_index, day in enumerate(week):
                if day == 0:
                    continue
                button = ttk.Button(
                    grid_frame,
                    text=str(day),
                    width=3,
                    command=lambda d=day: _pick(year, month, d),
                )
                button.grid(row=row_index, column=col_index)

    def _pick(y, m, d):
        result["date"] = (y, m, d)
        window.close()

    def _shift(delta):
        nonlocal month, year
        month += delta
        if month > 12:
            month, year = 1, year + 1
        elif month < 1:
            month, year = 12, year - 1
        _draw()

    rows = [
        [Text(message)],
        [Button("<", key="<"), Button(">", key=">")],
    ]
    window = Window(title, rows, finalize=True)
    grid_frame = tk.Frame(window.tk_root)
    grid_frame.grid(row=2, column=0, columnspan=2)
    cal_frame = tk.LabelFrame(window.tk_root, text="")
    # simpler: draw the day grid directly into grid_frame
    window["<"].widget.configure(command=lambda: _shift(-1))
    window[">"].widget.configure(command=lambda: _shift(1))
    _draw()
    window.read(close=True)
    return result["date"]


MsgBox = popup
