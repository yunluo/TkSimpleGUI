#!/usr/bin/env python3
"""The :class:`Window` class: layout hosting, event loop and element lookup."""

import queue
import threading
import time
import tkinter as tk
from tkinter import ttk

from .. import constants as C
from .. import _theming as theme_mod
from .. import settings as settings_mod
from ..elements.base import ContainerElement, Element
from ..elements.containers import Menu

try:
    from typing import Any, Dict, List, Optional, Tuple
except ImportError:
    Any = Dict = List = Optional = Tuple = None


class Window(object):
    """A top level window hosting a layout of elements.

    Typical usage::

        window = sg.Window("Title", layout, finalize=True)
        event, values = window.read()
        window["-INPUT-"].update("new text")
        window.close()

    The class is also a context manager: ``with sg.Window(...) as win:``
    finalizes on entry and closes on exit.
    """

    __slots__ = (
        "_title",
        "_layout",
        "_tk_root",
        "_finalized",
        "_closed",
        "_elements_by_key",
        "_event_queue",
        "_keep_on_top",
        "_modal",
        "_no_titlebar",
        "_grab_anywhere",
        "_return_keyboard_events",
        "_location",
        "_size",
        "_margins",
        "_background_color",
        "_icon",
        "_resizable",
        "_disable_close",
        "_element_justification",
        "_radio_groups",
        "_ttk_style",
        "_drag_offset",
    )

    _open_windows = []  # class level registry, access via active_windows()

    def __init__(
        self,
        title,
        layout=None,
        size=(None, None),
        location=(None, None),
        finalize=False,
        keep_on_top=False,
        modal=False,
        no_titlebar=False,
        grab_anywhere=False,
        return_keyboard_events=False,
        icon=None,
        background_color=None,
        margins=None,
        resizable=None,
        disable_close=False,
        element_justification=None,
    ):
        self._title = title
        self._layout = _validate_layout(layout)
        self._tk_root = None
        self._finalized = False
        self._closed = False
        self._elements_by_key = {}
        self._event_queue = queue.Queue()
        self._keep_on_top = (
            keep_on_top if keep_on_top is not None else settings_mod.settings.keep_on_top
        )
        self._modal = modal
        self._no_titlebar = no_titlebar
        self._grab_anywhere = grab_anywhere
        self._return_keyboard_events = return_keyboard_events
        self._location = location
        self._size = size
        self._margins = margins if margins is not None else settings_mod.settings.margins
        self._background_color = background_color
        self._icon = icon
        self._resizable = resizable
        self._disable_close = bool(disable_close)
        self._element_justification = element_justification
        self._radio_groups = {}
        self._ttk_style = None
        self._drag_offset = None
        if finalize:
            self.finalize()

    # --- properties -----------------------------------------------------------
    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value
        if self._root_alive():
            self._tk_root.title(value)

    @property
    def tk_root(self):
        """The underlying ``tk.Tk``/``tk.Toplevel`` (None until finalized)."""
        return self._tk_root

    @property
    def finalized(self):
        return self._finalized

    @property
    def was_closed(self):
        """True once :meth:`close` has been called (or the user closed it)."""
        return self._closed

    @property
    def ttk_style(self):
        return self._ttk_style

    @property
    def size(self):
        """The window size in pixels (use :meth:`set_size` to change it)."""
        if not self._root_alive():
            return (0, 0)
        return (self._tk_root.winfo_width(), self._tk_root.winfo_height())

    @size.setter
    def size(self, value):
        self.set_size(value)

    # --- class level registry ---------------------------------------------------
    @classmethod
    def active_windows(cls):
        """List of currently open windows (oldest first)."""
        return list(cls._open_windows)

    @classmethod
    def read_all_windows(cls, timeout=0, timeout_key=C.TIMEOUT_KEY):
        """Read from every open window once; returns (window, event, values).

        Returns ``None`` when no windows are open or every read timed out.
        """
        for window in list(cls._open_windows):
            event, values = window.read(timeout=timeout, timeout_key=timeout_key)
            if event != timeout_key:
                return (window, event, values)
        return None

    @classmethod
    def get_screen_size(cls):
        """``(width, height)`` of the primary screen in pixels."""
        root = None
        if cls._open_windows and cls._open_windows[0]._root_alive():
            root = cls._open_windows[0]._tk_root
        temporary = root is None
        if temporary:
            root = tk.Tk()
            root.withdraw()
        try:
            return (root.winfo_screenwidth(), root.winfo_screenheight())
        finally:
            if temporary:
                root.destroy()

    # --- construction -------------------------------------------------------------
    def finalize(self):
        """Create all tk widgets and show the window. Returns self."""
        if self._finalized:
            return self
        if self._closed:
            raise RuntimeError("cannot finalize a closed window")
        self._create_root()
        self._apply_window_options()
        try:
            content = tk.Frame(self._tk_root)
            bg = (
                self._background_color
                or theme_mod.theme_manager.background_color
            )
            if bg is not None:
                content.configure(background=bg)
            margins = self._margins
            self._tk_root.rowconfigure(0, weight=1)
            self._tk_root.columnconfigure(0, weight=1)
            content.grid(row=0, column=0, padx=margins[0], pady=margins[1], sticky="nsew")
            self._build_layout(self._layout, content)
        except Exception:
            self._destroy_root()
            self._mark_closed()
            raise
        self._finalized = True
        self._show()
        return self

    def _create_root(self):
        if Window._open_windows:
            self._tk_root = tk.Toplevel()
        else:
            self._tk_root = tk.Tk()
        Window._open_windows.append(self)
        self._tk_root.withdraw()
        self._ttk_style = ttk.Style(self._tk_root)
        theme_mod.theme_manager.configure_ttk(self._ttk_style)

    def _apply_window_options(self):
        root = self._tk_root
        root.title(self._title)
        window_kwargs = (
            theme_mod.theme_manager.window_kwargs()
            if self._background_color is None
            else {"background": self._background_color}
        )
        if window_kwargs:
            root.configure(**window_kwargs)
        if self._icon is not None:
            self._apply_icon(self._icon)
        else:
            self._apply_icon(
                (C.DEFAULT_BASE64_ICON, C.DEFAULT_BASE64_ICON_SMALL)
            )
        width, height = self._size
        if width is not None and height is not None:
            root.geometry("{}x{}".format(int(width), int(height)))
        x, y = self._location
        if x is not None and y is not None:
            current = root.geometry().split("+", 1)[0]
            root.geometry("{}+{}+{}".format(current, int(x), int(y)))
        if self._no_titlebar:
            root.overrideredirect(True)
        if self._keep_on_top:
            root.attributes("-topmost", True)
        if self._resizable is not None:
            if isinstance(self._resizable, (tuple, list)):
                root.resizable(bool(self._resizable[0]), bool(self._resizable[1]))
            else:
                root.resizable(bool(self._resizable), bool(self._resizable))
        if self._grab_anywhere:
            root.bind("<ButtonPress-1>", self._start_move)
            root.bind("<ButtonRelease-1>", self._stop_move)
            root.bind("<B1-Motion>", self._on_motion)
        if self._disable_close:
            root.protocol("WM_DELETE_WINDOW", lambda: None)
        else:
            root.protocol("WM_DELETE_WINDOW", lambda: self._post_event(C.WIN_CLOSED))
        if self._return_keyboard_events:
            root.bind("<Key>", self._on_keyboard_event)

    def _apply_icon(self, icon):
        """Set the icon from base64 data (one item or a tuple of sizes)."""
        try:
            if isinstance(icon, (bytes, str)):
                icon = (icon,)
            photos = [
                tk.PhotoImage(data=data, master=self._tk_root) for data in icon
            ]
            self._tk_root.iconphoto(True, *photos)
        except tk.TclError:
            pass

    def _show(self):
        root = self._tk_root
        root.update_idletasks()
        root.deiconify()
        if self._modal:
            root.grab_set()
            root.focus_force()

    # --- drag when grab_anywhere ------------------------------------------------
    def _start_move(self, event):
        self._drag_offset = (event.x, event.y)

    def _stop_move(self, _event):
        self._drag_offset = None

    def _on_motion(self, event):
        offset = self._drag_offset
        if offset:
            x = self._tk_root.winfo_x() - offset[0] + event.x
            y = self._tk_root.winfo_y() - offset[1] + event.y
            self._tk_root.geometry("+{}+{}".format(x, y))

    def _on_keyboard_event(self, event):
        self._post_event(str(event.keysym))

    # --- layout building -----------------------------------------------------------
    def _build_layout(self, layout, master):
        padding = settings_mod.settings.element_padding
        default_justification = self._element_justification
        expand_columns = set()
        expand_rows = set()
        for row_index, row in enumerate(layout):
            for col_index, element in enumerate(row):
                if not isinstance(element, Element):
                    raise TypeError(
                        "layout cell is not an Element: {!r}".format(element)
                    )
                self._register_element(element)
                element._build(master, self)
                if isinstance(element, Menu):
                    continue  # menubar is attached to the root, not gridded
                expand_x, expand_y = element._grid_into(
                    master, row_index, col_index, padding, default_justification
                )
                if expand_x:
                    expand_columns.add(col_index)
                if expand_y:
                    expand_rows.add(row_index)
        for column in expand_columns:
            master.columnconfigure(column, weight=1)
        for row in expand_rows:
            master.rowconfigure(row, weight=1)

    def _register_element(self, element):
        key = element.key
        if key is None:
            return
        if key in self._elements_by_key:
            raise ValueError("Duplicate element key: {!r}".format(key))
        self._elements_by_key[key] = element

    def _register_key(self, element):
        self._register_element(element)

    def _unregister_key(self, key):
        self._elements_by_key.pop(key, None)

    def radio_group_variable(self, group_id):
        """The shared ``StringVar`` for a radio button group."""
        if group_id not in self._radio_groups:
            self._radio_groups[group_id] = tk.StringVar(value="", master=self._tk_root)
        return self._radio_groups[group_id]

    # --- event plumbing ---------------------------------------------------------------
    def _post_event(self, key):
        """Queue an event (called by elements; user code uses ``write_event``)."""
        if not self._closed:
            self._event_queue.put(key)

    def write_event_value(self, value):
        """Queue a custom event from user code."""
        self._post_event(value)
        return self

    def perform_long_operation(self, func, end_key=C.DEFAULT_THREAD_KEY):
        """Run ``func`` in a background thread without blocking the GUI.

        With the default ``end_key`` the thread's return value is posted as
        an event (``end_key`` itself when the function returns ``None``;
        on an exception ``end_key`` is posted and the traceback re-raised in
        the worker thread). Pass ``end_key=None`` to receive this window as
        the ``func`` argument and post events yourself with
        :meth:`write_event_value`.
        """
        if end_key is None:
            def target():
                func(self)
        else:
            def target():
                try:
                    result = func()
                except Exception:
                    self._post_event(end_key)
                    raise
                self.write_event_value(result if result is not None else end_key)
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        return thread

    # --- reading -----------------------------------------------------------------------
    def read(self, timeout=None, close=False, timeout_key=C.TIMEOUT_KEY):
        """Pump events and return ``(event, values)``.

        :param timeout: milliseconds to wait before returning ``timeout_key``
        :param close: close the window after one event is processed
        :param timeout_key: the event string returned on timeout
        """
        if self._closed:
            return C.WIN_CLOSED, {}
        if not self._finalized:
            self.finalize()
        deadline = None if timeout is None else time.time() + timeout / 1000.0
        while True:
            if self._closed or not self._root_alive():
                self._mark_closed()
                return C.WIN_CLOSED, {}
            try:
                self._tk_root.update()
            except tk.TclError:
                self._mark_closed()
                return C.WIN_CLOSED, {}
            try:
                event = self._event_queue.get_nowait()
            except queue.Empty:
                event = None
            if event is None and deadline is not None and time.time() >= deadline:
                event = timeout_key
            if event is not None:
                values = self._collect_values()
                if close:
                    self.close()
                return event, values
            time.sleep(0.01)

    def _root_alive(self):
        try:
            return bool(self._tk_root.winfo_exists())
        except tk.TclError:
            return False

    def _mark_closed(self):
        self._closed = True
        if self in Window._open_windows:
            Window._open_windows.remove(self)

    def _collect_values(self):
        values = {}
        for key, element in self._elements_by_key.items():
            try:
                values[key] = element.get()
            except Exception:
                values[key] = None
        return values

    # --- element access ---------------------------------------------------------------
    def __getitem__(self, key):
        element = self._elements_by_key.get(key)
        if element is None:
            raise KeyError(
                "No element with key {!r} in window {!r}".format(key, self._title)
            )
        return element

    def __contains__(self, key):
        return key in self._elements_by_key

    def find_element(self, key):
        """Return the element with the given key or ``None``."""
        return self._elements_by_key.get(key)

    def find_element_with_focus(self):
        """Return the element holding the keyboard focus, or ``None``."""
        if not self._root_alive():
            return None
        focused = self._tk_root.focus_get()
        if focused is None:
            return None
        for element in self._elements_by_key.values():
            if element.widget is focused:
                return element
        return None

    def element(self, key):
        """Alias of :meth:`find_element`."""
        return self.find_element(key)

    FindElement = find_element

    def keys(self):
        """All registered element keys."""
        return list(self._elements_by_key.keys())

    def fill(self, values):
        """Push a dict of {key: value} into the matching elements."""
        for key, value in values.items():
            element = self._elements_by_key.get(key)
            if element is not None:
                element.update(value=value)
        return self

    def set_focus(self, element):
        """Give the focus to an element (instance or key)."""
        if isinstance(element, str):
            element = self._elements_by_key.get(element)
        if element is not None:
            element.set_focus()
        return self

    def hide_row(self, element):
        """Hide the element (instance or key)."""
        if isinstance(element, str):
            element = self._elements_by_key.get(element)
        if element is not None:
            element.hide()
        return self

    def unhide_row(self, element):
        """Show a previously hidden element (instance or key)."""
        if isinstance(element, str):
            element = self._elements_by_key.get(element)
        if element is not None:
            element.unhide()
        return self

    # --- window management ---------------------------------------------------------------
    def set_size(self, size):
        """Resize the window to ``(width, height)`` pixels."""
        if self._root_alive() and size is not None:
            self._tk_root.geometry("{}x{}".format(int(size[0]), int(size[1])))
        return self

    def set_min_size(self, size):
        """Set the smallest allowed window size ``(width, height)``."""
        if self._root_alive() and size is not None:
            self._tk_root.minsize(int(size[0]), int(size[1]))
        return self

    def current_location(self):
        """The window's ``(x, y)`` position on the screen."""
        if not self._root_alive():
            return (0, 0)
        return (self._tk_root.winfo_x(), self._tk_root.winfo_y())

    def move(self, x, y):
        """Move the window to the given screen position."""
        if self._root_alive():
            self._tk_root.geometry("+{}+{}".format(int(x), int(y)))
        return self

    def move_to_center(self):
        """Center the window on the screen."""
        if not self._root_alive():
            return self
        width, height = self.size
        if width <= 1:
            self._tk_root.update_idletasks()
            width = self._tk_root.winfo_reqwidth()
            height = self._tk_root.winfo_reqheight()
        x = max(0, (self._tk_root.winfo_screenwidth() - width) // 2)
        y = max(0, (self._tk_root.winfo_screenheight() - height) // 2)
        self._tk_root.geometry("+{}+{}".format(x, y))
        return self

    def maximize(self):
        """Maximize the window (fills the screen; the title bar stays)."""
        if self._root_alive():
            try:
                self._tk_root.state("zoomed")
            except tk.TclError:
                try:
                    self._tk_root.attributes("-zoomed", True)
                except tk.TclError:
                    pass
        return self

    def minimize(self):
        """Iconify the window to the task bar."""
        if self._root_alive():
            self._tk_root.iconify()
        return self

    def normal(self):
        """Restore the window to its normal size and position."""
        if self._root_alive():
            try:
                self._tk_root.state("normal")
            except tk.TclError:
                self._tk_root.deiconify()
        return self

    def restore(self):
        """Alias of :meth:`normal`."""
        return self.normal()

    def set_alpha_channel(self, alpha):
        """Set the window transparency (``0.0`` invisible - ``1.0`` opaque)."""
        if self._root_alive():
            try:
                self._tk_root.attributes("-alpha", float(alpha))
            except tk.TclError:
                pass
        return self

    def keep_on_top(self):
        """Keep this window above all others."""
        if self._root_alive():
            self._tk_root.attributes("-topmost", True)
        return self

    def hide(self):
        """Withdraw the window (it keeps running, just not shown)."""
        if self._root_alive():
            self._tk_root.withdraw()
        return self

    def unhide(self):
        """Show a hidden window again."""
        if self._root_alive():
            self._tk_root.deiconify()
        return self

    def set_icon(self, icon):
        """Set the window icon from base64 image data.

        Pass a single base64 payload or a tuple (small, large); ``None``
        restores the PySimpleGUI4 default badge.
        """
        self._icon = icon
        if self._root_alive():
            if icon is None:
                icon = (C.DEFAULT_BASE64_ICON, C.DEFAULT_BASE64_ICON_SMALL)
            self._apply_icon(icon)
        return self

    # --- clipboard / desktop integration -------------------------------------------------
    def clipboard_set(self, text):
        """Replace the system clipboard contents with ``text``."""
        if self._root_alive():
            self._tk_root.clipboard_clear()
            self._tk_root.clipboard_append(str(text))
        return self

    def clipboard_append(self, text):
        """Append ``text`` to the system clipboard."""
        if self._root_alive():
            self._tk_root.clipboard_append(str(text))
        return self

    def clipboard_get(self):
        """Return the current system clipboard contents."""
        if not self._root_alive():
            return ""
        try:
            return self._tk_root.clipboard_get()
        except tk.TclError:
            return ""

    def clipboard_clear(self):
        """Clear the system clipboard."""
        if self._root_alive():
            self._tk_root.clipboard_clear()
        return self

    # --- lifecycle -----------------------------------------------------------------------
    def refresh(self):
        """Process pending tk events without blocking."""
        if self._finalized and self._root_alive():
            self._tk_root.update()
        return self

    def bring_to_front(self):
        """Raise the window and give it focus."""
        if self._root_alive():
            self._tk_root.lift()
            self._tk_root.focus_force()
        return self

    def close(self):
        """Destroy the window and release its resources."""
        if self._closed:
            return self
        self._destroy_root()
        self._mark_closed()
        return self

    def _destroy_root(self):
        if self._tk_root is not None:
            try:
                self._tk_root.destroy()
            except tk.TclError:
                pass
            self._tk_root = None

    def __enter__(self):
        return self.finalize()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

    def __repr__(self):
        return "<Window {!r} finalized={} closed={}>".format(
            self._title, self._finalized, self._closed
        )


def _validate_layout(layout):
    """Normalize a layout (list of rows) raising on malformed input."""
    if layout is None:
        return []
    if not isinstance(layout, (list, tuple)):
        raise TypeError("layout must be a list of rows")
    rows = []
    for row in layout:
        if row is None:
            continue
        if not isinstance(row, (list, tuple)):
            row = [row]
        rows.append(list(row))
    return rows
