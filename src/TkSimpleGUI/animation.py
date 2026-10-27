#!/usr/bin/env python3
"""Small animation helpers built on :meth:`Window.after` (QPropertyAnimation
simplified). Every helper returns a cancellable ``_TimerHandle``; the window
must keep pumping events (``read``/``refresh``) for the animation to run.
"""

import tkinter as tk


def fade_in(window, duration_ms=300, steps=10, on_done=None):
    """Fade the window from transparent to opaque."""
    interval = max(1, int(duration_ms) // max(1, steps))
    step = 1.0 / max(1, steps)
    state = {"index": 0}

    def tick():
        state["index"] += 1
        alpha = min(1.0, state["index"] * step)
        try:
            window.tk_root.attributes("-alpha", alpha)
        except tk.TclError:
            handle.cancel()
            return
        if state["index"] >= steps:
            handle.cancel()
            if on_done is not None:
                on_done()

    handle = window.every(interval, tick)
    return handle


def fade_out(window, duration_ms=300, steps=10, on_done=None):
    """Fade the window towards invisible (does not close it)."""
    interval = max(1, int(duration_ms) // max(1, steps))
    step = 1.0 / max(1, steps)
    state = {"index": 0}

    def tick():
        state["index"] += 1
        alpha = max(0.0, 1.0 - state["index"] * step)
        try:
            window.tk_root.attributes("-alpha", alpha)
        except tk.TclError:
            handle.cancel()
            return
        if state["index"] >= steps:
            handle.cancel()
            if on_done is not None:
                on_done()

    handle = window.every(interval, tick)
    return handle


def slide(window, to_location, duration_ms=500, steps=10, on_done=None):
    """Move the window smoothly to ``to_location`` (x, y) on the screen."""
    if not window._root_alive():
        return None
    start_x = window.tk_root.winfo_x()
    start_y = window.tk_root.winfo_y()
    end_x, end_y = int(to_location[0]), int(to_location[1])
    interval = max(1, int(duration_ms) // max(1, steps))
    state = {"index": 0}

    def tick():
        state["index"] += 1
        done = state["index"] >= steps
        ratio = 1.0 if done else state["index"] / float(steps)
        x = int(start_x + (end_x - start_x) * ratio)
        y = int(start_y + (end_y - start_y) * ratio)
        window.move(x, y)
        if done:
            handle.cancel()
            if on_done is not None:
                on_done()

    handle = window.every(interval, tick)
    return handle


def animate_progress(window, bar, to_value, duration_ms=500, steps=10, on_done=None):
    """Animate a :class:`~TkSimpleGUI.elements.widgets.TProgressBar` (element
    or key) from its current value to ``to_value``."""
    element = window[bar] if isinstance(bar, str) else bar
    start = float(element.get() or 0)
    end = float(to_value)
    interval = max(1, int(duration_ms) // max(1, steps))
    state = {"index": 0}

    def tick():
        state["index"] += 1
        done = state["index"] >= steps
        ratio = 1.0 if done else state["index"] / float(steps)
        element.update(current_value=start + (end - start) * ratio)
        if done:
            handle.cancel()
            if on_done is not None:
                on_done()

    handle = window.every(interval, tick)
    return handle
