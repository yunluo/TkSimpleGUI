#!/usr/bin/env python3
"""Event manager for PySimpleGUI4.

:class:`PySimpleEvent` replaces the hand written ``while True`` read loop with
decorator based handlers::

    app = sg.PySimpleEvent()

    @app.bind_event("-OK-")
    def on_ok(window, values):
        sg.popup("clicked!")

    app.run_event(window)
"""

import functools

from . import constants as C
from .window.window import Window

try:
    from typing import Any, Callable, Dict, List, Optional, Tuple, Union
except ImportError:
    Any = Callable = Dict = List = Optional = Tuple = Union = None

_ENTER_KEYS = ("special 16777220", "special 16777221", "\r")


class PySimpleEvent(object):
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
                "event handler {!r} must be named with an 'on_' prefix".format(
                    func.__name__
                )
            )
        arg_names, arg_count = _handler_signature(func)
        entry = (func, arg_names, arg_count)
        if event not in self._event_handlers:
            self._event_handlers[event] = entry

    # --- dispatch --------------------------------------------------------------
    def apply_event(self, window, event, values):
        """Dispatch one event to its registered handler (if any)."""
        try:
            entry = self._event_handlers.get(event)
            if entry is None and event in _ENTER_KEYS:
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
            print("PySimpleEvent handler error for {!r}: {}".format(event, error))

    def run_event(self, main_window, close_event=None):
        """Run the GUI loop over all windows until the main window closes."""
        try:
            main_window.finalize()
            while True:
                result = Window.read_all_windows()
                if result is None:
                    break
                window, event, values = result
                if event in (C.WIN_CLOSED, close_event):
                    window.close()
                    if window is main_window:
                        break
                else:
                    self.apply_event(window, event, values)
        finally:
            main_window.close()


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
        key = "{}_{}_{}".format(str(func.__name__), str(args), str(kwargs))
        if key in instances:
            window = instances[key]
            if not window.was_closed:
                window.bring_to_front()
                return window
        new_window = func(*args, **kwargs)
        instances[key] = new_window
        return new_window

    return wrapper
