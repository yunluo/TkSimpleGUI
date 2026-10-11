#!/usr/bin/env python3
"""PySimpleGUI4 utility helpers."""

import os
import socket
import sys
import time


class Timer(object):
    """Simple stopwatch: call :meth:`start` then read :attr:`elapsed`."""

    def __init__(self):
        self._start = None
        self._stop = None

    def start(self):
        self._start = time.time()
        self._stop = None
        return self

    def stop(self):
        if self._start is not None:
            self._stop = time.time()
        return self

    @property
    def elapsed(self):
        """Seconds elapsed as a float (0 when not started)."""
        if self._start is None:
            return 0
        end = self._stop if self._stop is not None else time.time()
        return end - self._start

    @property
    def elapsed_ms(self):
        """Elapsed time in whole milliseconds."""
        return int(self.elapsed * 1000)

    def reset(self):
        self._start = None
        self._stop = None
        return self


class _ModuleTimer(object):
    """Backing state for the module level timer_start/timer_stop helpers."""

    _start = 0.0

    @classmethod
    def start(cls):
        cls._start = time.time()

    @classmethod
    def stop_ms(cls):
        return int((time.time() - cls._start) * 1000)


def timer_start():
    """Start the module level convenience timer."""
    _ModuleTimer.start()


def timer_stop():
    """Milliseconds elapsed since :func:`timer_start`."""
    return _ModuleTimer.stop_ms()


def formatted_datetime_now():
    """Current local time as ``YYYY-MM-DD HH:MM:SS``."""
    return time.strftime("%Y-%m-%d %H:%M:%S")


def rgb(red, green, blue):
    """Convert red/green/blue ints (clamped to 0-255) to a Tk color string."""
    values = []
    for component in (red, green, blue):
        component = int(component)
        if component < 0:
            component = 0
        elif component > 255:
            component = 255
        values.append(component)
    return "#{:02x}{:02x}{:02x}".format(values[0], values[1], values[2])


def running_windows():
    """True when running on Windows."""
    return sys.platform.startswith("win")


def running_linux():
    """True when running on Linux."""
    return sys.platform.startswith("linux")


def running_mac():
    """True when running on macOS."""
    return sys.platform.startswith("darwin")


def running_trinket():
    """True when running on the Trinket environment."""
    return sys.platform.startswith("linux") and socket.gethostname().startswith("pygame-")


def running_replit():
    """True when running on Replit."""
    return "REPL_OWNER" in os.environ and sys.platform.startswith("linux")
