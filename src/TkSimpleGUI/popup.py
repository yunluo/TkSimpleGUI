# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Popup dialogs for TkSimpleGUI.

Every popup is built from :class:`~TkSimpleGUI.window.Window` itself, so
popups automatically follow the active theme.
"""

from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from . import constants as C
from . import settings as settings_mod
from .elements.buttons import Button
from .elements.calendar import Calendar
from .elements.containers import Column
from .elements.widgets import Checkbox, Input, Listbox, Multiline, Spin, Text
from .window.window import Window

# A popup layout row is a list of elements (narrowed to Element's common base).
ElementRow = List[Any]



def _popup_window(
    title,
    lines,
    buttons=("OK",),
    auto_close_duration=None,
    no_buttons=False,
    size=(None, None),
):
    """Shared helper: build and read a simple popup window."""
    rows: List[ElementRow] = [[Text(line)] for line in lines]
    if not no_buttons and buttons:
        rows.append([Button(label, key=label) for label in buttons])
    window = Window(title, rows, size=size, finalize=True, modal=True)
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
    rows: List[ElementRow] = [[Text(line)] for line in lines]
    rows.append([Button(label, key=label) for label in buttons])
    window = Window(title, rows, finalize=True, modal=True)
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
    rows: List[ElementRow] = [[Multiline("\n".join(_message_lines(args)), size=size, key="-ML-")]]
    rows.append([Button("OK", key="OK"), Button("Cancel", key="Cancel")])
    window = Window(title, rows, finalize=True, modal=True)
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
    window = Window(title, rows, finalize=True, modal=True)
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

    options: Dict[str, Any] = {
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


def popup_get_date(message="Choose a date", title="", default_date=None, dateformat="%Y-%m-%d"):
    """Calendar chooser; returns a :class:`datetime.date` or None.

    ``default_date`` accepts a date or a ``(year, month, day)`` tuple
    (defaults to today).
    """
    import datetime as _dt

    if default_date is None:
        default_date = _dt.date.today()
    elif isinstance(default_date, tuple):
        default_date = _dt.date(*default_date)
    rows = [
        [Text(message)],
        [Calendar(default_date=default_date, dateformat=dateformat, key="-CAL-")],
        [Button("OK", key="OK"), Button("Cancel", key="Cancel")],
    ]
    window = Window(title, rows, finalize=True, modal=True)
    while True:
        event, _values = window.read()
        if event in (C.WIN_CLOSED, "Cancel"):
            window.close()
            return None
        if event == "OK":
            chosen = window["-CAL-"].date
            window.close()
            return chosen


# --- find / replace helpers (tk.Text search API) --------------------------------
def _as_text_widget(target):
    """The underlying tk.Text of a Multiline element (or the widget itself)."""
    text = getattr(target, "_text", None)
    return text if text is not None else target


def _text_find(widget, needle, start="1.0", case_sensitive=False):
    """First "line.col" index of ``needle`` in a tk.Text, or None."""
    widget = _as_text_widget(widget)
    needle = str(needle)
    if not needle:
        return None
    pos = widget.search(needle, start, stopindex="end", nocase=not case_sensitive)
    return pos or None


def _text_replace_all(widget, needle, replacement, case_sensitive=False):
    """Replace every occurrence in a tk.Text; returns the replacement count.

    The search resumes after each inserted replacement so replacements that
    contain the needle cannot loop forever.
    """
    widget = _as_text_widget(widget)
    needle = str(needle)
    replacement = str(replacement)
    if not needle:
        return 0
    count = 0
    start = "1.0"
    step = len(replacement) or 1
    while True:
        pos = widget.search(needle, start, stopindex="end", nocase=not case_sensitive)
        if not pos:
            break
        widget.delete(pos, f"{pos}+{len(needle)}c")
        widget.insert(pos, replacement)
        count += 1
        start = f"{pos}+{step}c"
    return count


def popup_find(multiline, title="Find Text", case_sensitive=False):
    """Find text in a :class:`~TkSimpleGUI.elements.widgets.Multiline`.

    The first match from the top is selected and scrolled into view.
    Returns the match's ``"line.col"`` index, or None when not found /
    cancelled.
    """
    rows = [
        [Text("Find what:")],
        [Input("", key="-IN-", size=(40, 1))],
        [Button("Find", key="Find"), Button("Cancel", key="Cancel")],
    ]
    window = Window(title, rows, finalize=True, modal=True)
    window["-IN-"].widget.focus_set()
    event, values = window.read(close=True)
    if event != "Find":
        return None
    widget = _as_text_widget(multiline)
    needle = values.get("-IN-", "")
    pos = _text_find(widget, needle, case_sensitive=case_sensitive)
    if pos:
        widget.tag_remove("sel", "1.0", "end")
        widget.tag_add("sel", pos, f"{pos}+{len(needle)}c")
        widget.mark_set("insert", pos)
        widget.see(pos)
        widget.focus_set()
    return pos


def popup_replace(multiline, title="Replace", case_sensitive=False):
    """Replace-all dialog for a Multiline element.

    Returns the number of replacements, or None when cancelled. The search
    resumes after each inserted replacement, so replacing ``a`` with ``aa``
    terminates.
    """
    rows = [
        [Text("Find what:"), Input("", key="-IN-", size=(30, 1))],
        [Text("Replace with:"), Input("", key="-REP-", size=(30, 1))],
        [Button("Replace All", key="RA"), Button("Cancel", key="Cancel")],
    ]
    window = Window(title, rows, finalize=True, modal=True)
    window["-IN-"].widget.focus_set()
    event, values = window.read(close=True)
    if event != "RA":
        return None
    widget = _as_text_widget(multiline)
    was_disabled = str(widget.cget("state")) == "disabled"
    widget.configure(state="normal")
    count = _text_replace_all(
        widget,
        values.get("-IN-", ""),
        values.get("-REP-", ""),
        case_sensitive=case_sensitive,
    )
    widget.configure(state="disabled" if was_disabled else "normal")
    return count


def popup_get_font(
    message="Pick a font",
    title="",
    default_font=("Helvetica", 12),
    include_bold_italic=False,
):
    """Font chooser (Delphi TFontDialog equivalent).

    Returns ``(family, size)`` — or ``(family, size, bold, italic)`` when
    ``include_bold_italic`` is True — or None on cancel.
    """
    import tkinter.font as tkfont

    family, size = default_font[0], int(default_font[1])
    bold = len(default_font) > 2 and "bold" in default_font[2:]
    italic = len(default_font) > 2 and "italic" in default_font[2:]

    picker_column = [Listbox([], key="-FONTS-", size=(26, 10), enable_events=True)]
    option_rows: List[ElementRow] = [
        [Text("Size")],
        [Spin([str(n) for n in range(1, 101)], initial_value=str(size), key="-SIZE-")],
    ]
    if include_bold_italic:
        option_rows.append([Checkbox("Bold", key="-BOLD-", default=bold)])
        option_rows.append([Checkbox("Italic", key="-ITALIC-", default=italic)])
    option_rows.append(
        [Multiline("AaBbYyZz 123", key="-PREVIEW-", size=(20, 3), font=(family, size))]
    )
    rows: List[ElementRow] = [
        [Text(message)],
        [Column(picker_column), Column(option_rows)],
        [Button("OK", key="OK"), Button("Cancel", key="Cancel")],
    ]
    window = Window(title, rows, finalize=True, modal=True)
    families = sorted(tkfont.families(root=window.tk_root))
    listbox = window["-FONTS-"]
    listbox.update(values=families)
    if family in families:
        listbox.update(set_to_index=families.index(family))

    def _current_font():
        chosen = listbox.get()
        picked_family = chosen[0] if chosen else family
        try:
            picked_size = int(window["-SIZE-"].get())
        except (TypeError, ValueError):
            picked_size = size
        picked_bold = bool(window["-BOLD-"].get()) if include_bold_italic else bold
        picked_italic = (
            bool(window["-ITALIC-"].get()) if include_bold_italic else italic
        )
        flags = []
        if picked_bold:
            flags.append("bold")
        if picked_italic:
            flags.append("italic")
        return picked_family, picked_size, tuple(flags)

    def _refresh_preview(_window=None, _event=None, _values=None):
        picked = _current_font()
        window["-PREVIEW-"].widget.configure(font=(picked[0], picked[1]) + picked[2])

    window["-SIZE-"].widget.configure(command=_refresh_preview)
    if include_bold_italic:
        window["-BOLD-"].widget.configure(command=_refresh_preview)
        window["-ITALIC-"].widget.configure(command=_refresh_preview)

    result = None
    while True:
        event, _values = window.read()
        if event in (C.WIN_CLOSED, "Cancel"):
            break
        if event in ("-FONTS-", "-SIZE-", "-BOLD-", "-ITALIC-"):
            _refresh_preview()
            continue
        if event == "OK":
            picked = _current_font()
            if include_bold_italic:
                result = (picked[0], picked[1], picked[2])
            else:
                result = (picked[0], picked[1])
            break
    window.close()
    return result


MsgBox = popup
