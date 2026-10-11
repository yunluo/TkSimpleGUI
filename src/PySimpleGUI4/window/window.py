#!/usr/bin/env python3
"""The :class:`Window` class: layout hosting, event loop and element lookup."""

import queue
import threading
import time
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional, Tuple, Union

from .. import constants as C
from .. import _theming as theme_mod
from .. import settings as settings_mod
from ..actions import ActionList
from ..elements.base import Element, build_popup_menu
from ..elements.containers import Menu

# A Window size or on-screen position as (x, y) pixels.
WindowPoint = Tuple[int, int]
# Sizes/locations accept None components ("let the wm decide").
OptionalPoint = Tuple[Optional[int], Optional[int]]



class Window(object):
    """A top level window hosting a layout of elements.

    Typical usage::

        window = sg.Window("Title", layout, finalize=True)
        event, values = window.read()
        window["-INPUT-"].update("new text")
        window.close()

    The class is also a context manager: ``with sg.Window(...) as win:``
    finalizes on entry and closes on exit.

    Typing note: ``_tk_root`` is ``None`` until :meth:`finalize` (or the
    auto-finalize inside :meth:`read`) and cleared on close, but every
    method that touches it guards with :meth:`_root_alive` first, so it is
    annotated as non-optional to keep the call sites narrow.
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
        "_right_click_menu",
        "_popup_menu",
        "_action_by_key",
        "_action_by_text",
        "_event_binds",
        "_radio_groups",
        "_toggle_groups",
        "_ttk_style",
        "_drag_offset",
    )

    _open_windows: List["Window"] = []  # class level registry

    # Typed views of the slots (runtime stays __slots__-based).
    _title: str
    _layout: List[List[Element]]
    _tk_root: Union[tk.Tk, tk.Toplevel]
    _finalized: bool
    _closed: bool
    _elements_by_key: Dict[Any, Element]
    _event_queue: "queue.Queue[Any]"
    _keep_on_top: Optional[bool]
    _modal: bool
    _no_titlebar: bool
    _grab_anywhere: bool
    _return_keyboard_events: bool
    _location: OptionalPoint
    _size: OptionalPoint
    _margins: Tuple[int, int]
    _background_color: Optional[str]
    _icon: Any
    _resizable: Optional[Union[bool, Tuple[bool, bool]]]
    _disable_close: bool
    _element_justification: Optional[str]
    _right_click_menu: Optional[list]
    _popup_menu: Optional[tk.Menu]
    _action_by_key: Dict[Any, Any]
    _action_by_text: Dict[str, Any]
    _event_binds: List[Tuple[str, Optional[Any]]]
    _radio_groups: Dict[Any, tk.StringVar]
    _toggle_groups: Dict[Any, List[Any]]
    _ttk_style: ttk.Style
    _drag_offset: Optional[Tuple[int, int]]

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
        right_click_menu=None,
        actions=None,
    ):
        self._title = title
        self._layout = _validate_layout(layout)
        self._tk_root = None  # ty: ignore[invalid-assignment]
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
        self._right_click_menu = right_click_menu
        self._popup_menu = None
        self._action_by_key = {}
        self._action_by_text = {}
        self._event_binds = []
        self._radio_groups = {}
        self._toggle_groups = {}
        self._ttk_style = None  # ty: ignore[invalid-assignment]
        self._drag_offset = None
        if actions is not None:
            self.set_actions(actions)
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
        borrowed = None
        if cls._open_windows and cls._open_windows[0]._root_alive():
            borrowed = cls._open_windows[0]._tk_root
        if borrowed is not None:
            return (borrowed.winfo_screenwidth(), borrowed.winfo_screenheight())
        temporary = tk.Tk()
        temporary.withdraw()
        try:
            return (temporary.winfo_screenwidth(), temporary.winfo_screenheight())
        finally:
            temporary.destroy()

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
            root.geometry(f"{int(width)}x{int(height)}")
        x, y = self._location
        if x is not None and y is not None:
            current = root.geometry().split("+", 1)[0]
            root.geometry(f"{current}+{int(x)}+{int(y)}")
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
        if self._right_click_menu is not None:
            self._popup_menu = build_popup_menu(
                self, root, self._right_click_menu
            )
            root.bind("<Button-3>", self._show_popup_menu)
        if self._disable_close:
            root.protocol("WM_DELETE_WINDOW", lambda: None)
        else:
            root.protocol("WM_DELETE_WINDOW", lambda: self._post_event(C.WIN_CLOSED))
        if self._return_keyboard_events:
            root.bind("<Key>", self._on_keyboard_event)
        for shortcut, key in self._event_binds:
            root.bind(shortcut, lambda _e, k=key: self._post_event(k))

    def _show_popup_menu(self, event):
        if self._popup_menu is not None:
            try:
                self._popup_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self._popup_menu.grab_release()
        return "break"

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
            self._tk_root.geometry(f"+{x}+{y}")

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
                        f"layout cell is not an Element: {element!r}"
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
            raise ValueError(f"Duplicate element key: {key!r}")
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

    def _press_toggle(self, group_id, button):
        """Exclusive-press bookkeeping for toggle buttons sharing ``group_id``."""
        group = self._toggle_groups.setdefault(group_id, [])
        for other in group:
            if other is not button:
                other._set_down(False)
        if button not in group:
            group.append(button)

    # --- event plumbing ---------------------------------------------------------------
    def set_actions(self, actions):
        """Register :class:`~PySimpleGUI4.actions.Action` objects.

        Menu/right-click item texts matching an action's text are normalized
        to its key, shortcuts are bound as keyboard events, and the action's
        callback fires automatically when its event is read. Returns self.
        """
        self._action_by_key = {}
        self._action_by_text = {}
        if isinstance(actions, ActionList):
            actions = list(actions)
        for action in actions:
            self._action_by_key[action.key] = action
            self._action_by_text[action.text] = action
            if action.shortcut:
                self.bind(action.shortcut, action.key)
        return self

    def bind(self, shortcut, key=None):
        """Bind a tk event pattern (e.g. ``"<Control-o>"``) to an event key.

        The binding works before and after :meth:`finalize`. Returns self.
        """
        self._event_binds.append((shortcut, key))
        if self._root_alive():
            self._tk_root.bind(shortcut, lambda _e, k=key: self._post_event(k))
        return self

    def _dispatch_action(self, event, values):
        """Auto-fire the callback of the action matching ``event``."""
        if not self._action_by_key or not isinstance(event, str):
            return
        action = self._action_by_key.get(event)
        if action is not None:
            action.trigger(self, values)

    def _post_event(self, key):
        """Queue an event (called by elements; user code uses ``write_event``)."""
        if not self._closed:
            if self._action_by_text and isinstance(key, str):
                action = self._action_by_text.get(key)
                if action is not None:
                    key = action.key
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

    # --- timers (Delphi TTimer equivalent) --------------------------------------------
    def after(self, interval_ms, callback):
        """Run ``callback`` once after ``interval_ms`` on the tk event loop.

        Returns a :class:`_TimerHandle` — call ``.cancel()`` to abort. The
        callback only fires while the window pumps events (``read``/``refresh``).
        """
        handle = _TimerHandle(self)
        handle._id = self._tk_root.after(
            int(interval_ms),
            lambda: self._run_timer(handle, callback, repeat_ms=None),
        )
        return handle

    def every(self, interval_ms, callback):
        """Call ``callback`` every ``interval_ms`` until cancelled or closed.

        Returns a :class:`_TimerHandle` — call ``.cancel()`` to stop.
        """
        handle = _TimerHandle(self)
        handle._id = self._tk_root.after(
            int(interval_ms),
            lambda: self._run_timer(handle, callback, repeat_ms=int(interval_ms)),
        )
        return handle

    def _run_timer(self, handle, callback, repeat_ms):
        if handle._cancelled or self._closed or not self._root_alive():
            handle._id = None
            return
        try:
            callback()
        finally:
            if (
                not handle._cancelled
                and repeat_ms is not None
                and not self._closed
                and self._root_alive()
            ):
                handle._id = self._tk_root.after(
                    repeat_ms,
                    lambda: self._run_timer(handle, callback, repeat_ms),
                )
            else:
                handle._id = None

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
                self._dispatch_action(event, values)
                if close:
                    self.close()
                return event, values
            time.sleep(0.01)

    def _root_alive(self):
        if self._tk_root is None:
            return False
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
                f"No element with key {key!r} in window {self._title!r}"
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
            self._tk_root.geometry(f"{int(size[0])}x{int(size[1])}")
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
            self._tk_root.geometry(f"+{int(x)}+{int(y)}")
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
        self._tk_root.geometry(f"+{x}+{y}")
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

    def set_fullscreen(self, fullscreen=True):
        """Toggle true fullscreen (no title bar, covers the whole screen)."""
        if self._root_alive():
            self._tk_root.attributes("-fullscreen", bool(fullscreen))
        return self

    def make_toolwindow(self, toolwindow=True):
        """Windows-only small tool window (no task bar entry)."""
        if self._root_alive():
            try:
                self._tk_root.attributes("-toolwindow", bool(toolwindow))
            except tk.TclError:
                pass
        return self

    def transient(self, parent_window=None):
        """Mark this window as a transient (dialog) of ``parent_window``.

        The window manager groups it above its parent and keeps it on the
        parent's screen; pass the parent :class:`Window` or None to clear
        the hint (the window becomes independent again).
        """
        if not self._root_alive():
            return self
        if parent_window is None:
            self._tk_root.transient(None)  # clear the WM hint
        else:
            parent_root = getattr(parent_window, "tk_root", parent_window)
            if parent_root is not None:
                self._tk_root.transient(parent_root)
        return self

    def stack_above(self, other_window):
        """Keep this window stacked above ``other_window`` (WM transient hint)."""
        if self._root_alive():
            other_root = getattr(other_window, "tk_root", other_window)
            if other_root is not None:
                self._tk_root.transient(other_root)
        return self

    def set_max_size(self, size):
        """Limit the largest allowed window size ``(width, height)``."""
        if self._root_alive() and size is not None:
            self._tk_root.maxsize(int(size[0]), int(size[1]))
        return self

    def bell(self):
        """Ring the system bell."""
        if self._root_alive():
            self._tk_root.bell()
        return self

    # --- selection (PRIMARY selection, distinct from clipboard) --------------------------
    def selection_get(self):
        """Read the PRIMARY selection (text highlighted anywhere)."""
        if not self._root_alive():
            return ""
        try:
            return self._tk_root.selection_get(selection="PRIMARY")
        except tk.TclError:
            return ""

    def selection_set(self, text):
        """Own the PRIMARY selection with ``text`` (e.g. highlighted text)."""
        if self._root_alive():
            self._tk_root.selection_clear()
            self._tk_root.selection_own()
            self._tk_root.selection_handle(
                lambda _kind, _fmt: str(text)
            )
        return self

    # --- ttk style hooks -------------------------------------------------------------------
    def configure_style(self, style=".", **options):
        """Advanced hook: ``style.configure`` on the window's ttk style.

        Tweak the ttk engine beyond what ThemeManager offers::

            window.configure_style("TButton", padding=(12, 6))
        """
        if self._root_alive():
            self._ttk_style.configure(style, **options)
        return self

    def map_style(self, style, **query_options):
        """Advanced hook: ``style.map`` for dynamic state colors::

            window.map_style("TButton",
                             background=[("active", "#3a7bd5")])
        """
        if self._root_alive():
            self._ttk_style.map(style, **query_options)
        return self

    # --- clipboard / desktop integration -------------------------------------------------
    def toast(
        self,
        message,
        title="",
        duration_ms=2500,
        background_color="#333333",
        text_color="#ffffff",
        font=None,
        location=None,
    ):
        """Show an in-window toast notification (bottom-right by default).

        A borderless Toplevel with a fade-in/out animation; it closes itself
        after ``duration_ms`` and never steals focus. Events keep flowing
        through :meth:`read` while the toast is visible. Returns the toast
        :class:`tk.Toplevel` (already scheduled to self-destruct).
        """
        if not self._root_alive():
            return None
        toast = tk.Toplevel(self._tk_root)
        toast.wm_overrideredirect(True)
        toast.attributes("-topmost", True)
        body = tk.Label(
            toast,
            text=f"{title}\n{message}" if title else str(message),
            background=background_color,
            foreground=text_color,
            font=font or ("Helvetica", 10),
            justify="left",
            padx=14,
            pady=10,
        )
        body.pack()
        self._tk_root.update_idletasks()
        toast.update_idletasks()
        margin = 16
        if location is not None:
            x, y = int(location[0]), int(location[1])
        else:
            x = self._tk_root.winfo_rootx() + self._tk_root.winfo_width() \
                - toast.winfo_reqwidth() - margin
            y = self._tk_root.winfo_rooty() + self._tk_root.winfo_height() \
                - toast.winfo_reqheight() - margin
        toast.wm_geometry(f"+{x}+{y}")

        steps = 8
        interval = max(20, int(duration_ms * 0.15) // steps)

        def fade(final_alpha, then=None):
            state = {"index": 0}

            def tick():
                state["index"] += 1
                ratio = state["index"] / float(steps)
                alpha = final_alpha * ratio
                try:
                    toast.attributes("-alpha", alpha)
                except tk.TclError:
                    return
                if state["index"] >= steps:
                    if then is not None:
                        then()
                else:
                    toast.after(interval, tick)

            tick()

        def hold_then_fade_out():
            toast.after(int(duration_ms * 0.7), lambda: fade(0.0, then=toast.destroy))

        try:
            toast.attributes("-alpha", 0.0)
        except tk.TclError:
            hold_then_fade_out()  # no alpha support: just show and destroy
            return toast
        fade(1.0, then=hold_then_fade_out)
        return toast
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
            self._tk_root = None  # ty: ignore[invalid-assignment]

    def __enter__(self):
        return self.finalize()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

    def __repr__(self):
        return f"<Window {self._title!r} finalized={self._finalized} closed={self._closed}>"


class _TimerHandle(object):
    """Cancellable handle returned by :meth:`Window.after` / :meth:`Window.every`."""

    __slots__ = ("_window", "_id", "_cancelled")

    def __init__(self, window):
        self._window = window
        self._id = None
        self._cancelled = False

    def cancel(self):
        """Stop the timer (safe to call more than once)."""
        self._cancelled = True
        if self._id is not None and self._window._root_alive():
            try:
                self._window._tk_root.after_cancel(self._id)
            except tk.TclError:
                pass
            self._id = None
        return self

    @property
    def active(self):
        return not self._cancelled and self._id is not None


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
