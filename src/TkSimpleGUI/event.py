# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Event manager for TkSimpleGUI.

:class:`TkSimpleEvent` replaces the hand written ``while True`` read loop with
decorator based handlers::

    app = sg.TkSimpleEvent()

    @app.bind_event("-OK-")
    def on_ok(window, values):
        sg.popup("clicked!")

    app.run_event(window)
"""

import functools
import time
from typing import Optional

from . import constants as C
from .window.window import Window


_ENTER_KEYS = ("special 16777220", "special 16777221", "\r")


class TkSimpleEvent(object):
    """Decorator based dispatch of window events to handler functions.

    A handler function may be written with any of these signatures:

    1. ``on_x()`` - no arguments
    2. ``on_x(window)`` - the window
    3. ``on_x(event)`` - the event key
    4. ``on_x(values)`` - the values dict
    5. ``on_x(window, values)`` / ``on_x(window, event, values)`` - any
       combination of the names ``window``, ``event`` and ``values``
    """

    def __init__(self):
        self._event_handlers = {}

    @property
    def get_events(self):
        """Read-only mapping of event key to handler function."""
        return dict((k, entry[0]) for k, entry in self._event_handlers.items())

    # --- registration --------------------------------------------------------
    def bind_event(self, event_names):
        """Decorator binding a handler to one event key or a list of keys."""

        def decorator(func):
            if isinstance(event_names, str):
                self._add_event(event_names, func)
            elif isinstance(event_names, (list, tuple)):
                for event_name in event_names:
                    self._add_event(event_name, func)
            else:
                raise TypeError("event_names must be a string or a list of strings")
            return func

        return decorator

    def _add_event(self, event, func):
        if not str(func.__name__).startswith("on_"):
            raise ValueError(
                f"event handler {func.__name__!r} must be named with an 'on_' prefix"
            )
        arg_names, arg_count = _handler_signature(func)
        entry = (func, arg_names, arg_count)
        if event not in self._event_handlers:
            self._event_handlers[event] = entry

    # --- dispatch --------------------------------------------------------------
    def apply_event(self, window, event, values):
        """Dispatch one event to its registered handler (if any).

        Timer ticks (``TIMEOUT_KEY``) and other no-handler events are
        dropped silently; ``window`` may be ``None`` on timeout results.
        """
        if event == C.TIMEOUT_KEY:
            return
        try:
            entry = self._event_handlers.get(event)
            if entry is None and event in _ENTER_KEYS and window is not None:
                focused = window.find_element_with_focus()
                if focused is not None and focused.key is not None:
                    entry = self._event_handlers.get(focused.key)
            if entry is None:
                return
            func, arg_names, arg_count = entry
            if arg_count == 0:
                func()
                return
            args = []
            if arg_count == 1:
                single = arg_names[0]
                if single == "window":
                    args.append(window)
                elif single == "event":
                    args.append(event)
                else:
                    args.append(values)
            else:
                for name in arg_names[:arg_count]:
                    if name == "window":
                        args.append(window)
                    elif name == "event":
                        args.append(event)
                    elif name == "values":
                        args.append(values)
            func(*args)
        except Exception as error:  # keep the loop alive on handler errors
            print(f"TkSimpleEvent handler error for {event!r}: {error}")

    def run_event(self, main_window, close_event=None):
        """Run the single application event loop until every window closes.

        This is the framework's own loop — user code never writes
        ``while True``. Events from ALL open windows flow through one global
        bus; each one is dispatched to its ``on_*`` handler here. ``Window``
        title-bar closes become WIN_CLOSED events (the window leaves the
        registry automatically); once no window is left the loop ends.
        ``main_window`` is only the anchor that gets created first; extra
        windows opened inside handlers participate automatically.
        """
        main_window.finalize()
        try:
            while True:
                window, event, values = Window.read_all_windows()
                # exit ONLY on the all-windows-closed notification; a
                # (None, TIMEOUT_KEY, {}) result just means the bus was
                # empty this tick — keep pumping
                if window is None and event is C.WIN_CLOSED:
                    break
                if close_event is not None and event == close_event and window is main_window:
                    Window.close_all()
                    break
                self.apply_event(window, event, values)
        finally:
            Window.close_all()


# --- application-wide default event manager ------------------------------------
# sg.Window(...).run() / sg.SystemTray(...).run() use this instance when no
# explicit app is passed; @app.bind_event handlers registered on it are
# picked up automatically.
_default_app: Optional["TkSimpleEvent"] = None


def default_app() -> "TkSimpleEvent":
    """The global default event manager (created on first use)."""
    global _default_app
    if _default_app is None:
        _default_app = TkSimpleEvent()
    return _default_app


def run_application(anchor, app: Optional["TkSimpleEvent"] = None, close_event=None):
    """Run the application loop with ``anchor`` as the root object.

    ``anchor`` is either a :class:`~TkSimpleGUI.window.Window` (a normal
    main window) or a :class:`~TkSimpleGUI.window.SystemTray` (a tray-only
    application). This is what ``.run()`` calls on both.
    """
    from .window.system_tray import SystemTray

    manager = app if app is not None else default_app()
    if isinstance(anchor, SystemTray):
        # tray-only application: there is no window to finalize; the loop
        # pumps the tk root (tray WndProc events + after timers) directly
        anchor._ensure_pump_root()
        try:
            while True:
                # pump tk with a bounded wait so after() timers fire even
                # when no windows are open
                if Window._open_windows:
                    Window.read_all_windows(timeout=30)
                else:
                    anchor._tk_root.update()
                    time.sleep(0.02)
                # dispatch tray events through the same manager
                if not anchor._created:
                    break  # tray removed: application over
                tray_event, _payload = anchor.read(timeout=0)
                if tray_event not in (None, C.TIMEOUT_KEY):
                    manager.apply_event(anchor, tray_event, {})
                if not anchor._created:
                    break
        finally:
            anchor.close()
            Window.close_all()
        return manager
    # window-anchored application
    return manager.run_event(anchor, close_event=close_event)


def _handler_signature(func):
    """(arg_names, arg_count) of a handler function."""
    code = func.__code__
    return tuple(code.co_varnames[: code.co_argcount]), code.co_argcount


def singleton_window(func):
    """Decorator making a window-creating function return a single instance.

    Repeated calls bring the existing window to the front instead of creating
    a second one, until it has been closed.
    """
    instances = {}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        key = f"{str(func.__name__)}_{str(args)}_{str(kwargs)}"
        if key in instances:
            window = instances[key]
            if not window.was_closed:
                window.bring_to_front()
                return window
        new_window = func(*args, **kwargs)
        instances[key] = new_window
        return new_window

    return wrapper
