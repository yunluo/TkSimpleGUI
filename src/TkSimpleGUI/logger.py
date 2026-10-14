#!/usr/bin/env python3
"""Log lines with levels and colors, rendered into an Output / Multiline box.

TkSimpleGUI has no separate log window: the log box *is* a widget —
:class:`~TkSimpleGUI.Output` (a read-only Multiline). This module puts the
logging layer on top of that widget instead of inventing a second output
path:

- :class:`Logger` — levels (debug / info / success / warning / error /
  critical), an optional timestamp, the semantic color per level, a line
  cap (ring buffer), an optional file mirror, and marshalling of lines that
  arrive from worker threads (``start_task`` style work logs safely).
- :func:`log` — the one-liner: ``ts.log("connected")`` writes into the
  window's Output element, no logger object needed.

Level colors reuse the Element Plus semantics shared with Alert / Result
(``error`` is the same red as an error alert), so a log panel and the rest
of the UI speak one visual language::

    out = ts.Output(size=(90, 12), key="-LOG-")
    out.log("sampling started")                 # INFO
    out.log("channel 3 noisy", level="warning") # amber
    gl = out.logger(max_lines=500, mirror="run.log")
    gl.attach_logging("INFO")                   # stdlib logging lands here too
"""

import contextlib
import logging
import queue
import threading
import time
import traceback
from typing import Any, Dict, List, Optional, Tuple

from .elements._paint import DANGER, INFO, SUCCESS, WARNING

# --- level tables -------------------------------------------------------------
# "info" renders in the widget's own (theme following) text color; the rest
# are the semantic colors shared with the display elements.
_LEVEL_COLORS: Dict[str, Optional[str]] = {
    "debug": INFO,
    "info": None,
    "success": SUCCESS,
    "warning": WARNING,
    "error": DANGER,
    "critical": DANGER,
}

_LEVEL_RANK = {
    "debug": 10,
    "info": 20,
    "success": 20,
    "warning": 30,
    "error": 40,
    "critical": 50,
}

_LABEL_WIDTH = 7  # "warning" is the longest level name


def _level_name(level) -> str:
    """Normalise a level argument to a known level name."""
    name = str(level or "info").lower()
    return name if name in _LEVEL_RANK else "info"


def _level_for_logging(levelno: int) -> str:
    """Map a :mod:`logging` level number to a TkSimpleGUI log level."""
    if levelno >= logging.CRITICAL:
        return "critical"
    if levelno >= logging.ERROR:
        return "error"
    if levelno >= logging.WARNING:
        return "warning"
    if levelno >= logging.INFO:
        return "info"
    return "debug"


class Logger:
    """A formatted, colored log view over one Output / Multiline element.

    Differences from :class:`logging.Logger` worth knowing: this object
    *renders* into a widget (it is not a hierarchical logger), it always
    stamps every line the same way, and it can hand the standard library's
    records to the widget through :meth:`attach_logging`::

        logger = ts.Logger(window["-LOG-"], max_lines=500)
        logger.info("connected")
        logger.error("sync failed")
    """

    __slots__ = (
        "_element",
        "_timestamp",
        "_max_lines",
        "_min_level",
        "_colors",
        "_mirror",
        "_mirror_owned",
        "_queue",
        "_timer",
        "_drain_ms",
        "_attachments",
    )

    _element: Any
    _mirror: Any
    _timer: Any
    _attachments: List[Tuple[Any, Any, int]]
    _queue: "queue.Queue[Tuple[Tuple[Any, ...], str, Optional[str], Any]]"

    def __init__(
        self,
        element,
        timestamp="%H:%M:%S",
        max_lines=2000,
        min_level="debug",
        colors=None,
        mirror=None,
        drain_ms=100,
    ):
        if element is None or not hasattr(element, "print"):
            raise TypeError(
                "Logger needs a Multiline / Output element to write into"
            )
        self._element = element
        self._timestamp = "" if timestamp is False else timestamp
        self._max_lines = None if max_lines is None else max(1, int(max_lines))
        self._min_level = _level_name(min_level)
        self._colors = dict(colors) if colors else {}
        self._queue = queue.Queue()
        self._timer = None
        self._drain_ms = None if drain_ms is None else max(20, int(drain_ms))
        self._attachments = []
        self._mirror_owned = False
        if mirror is None:
            self._mirror = None
        elif hasattr(mirror, "write"):
            self._mirror = mirror
        else:
            # kept open for the logger's lifetime; close() releases it
            self._mirror = open(str(mirror), "a", encoding="utf-8")  # noqa: SIM115
            self._mirror_owned = True
        self._start_drain_timer()

    # --- writing ---------------------------------------------------------------
    def write(self, *args, level="info", color=None, timestamp=None):
        """Append one line; safe to call from a worker thread.

        ``level`` picks the semantic color (and the level filter),
        ``color`` overrides it for this line, ``timestamp`` overrides the
        stamp format (``False`` / ``""`` omits the stamp).
        """
        name = _level_name(level)
        payload = (args, name, color, timestamp)
        if threading.current_thread() is threading.main_thread():
            self._ensure_drain_timer()
            self._emit(*payload)
        else:
            # off the Tk thread: queue it, the drain timer writes it back
            self._queue.put(payload)
        return self

    def log(self, *args, **kwargs):
        """Alias of :meth:`write` (reads naturally as ``logger.log(...)``)."""
        return self.write(*args, **kwargs)

    def debug(self, *args, **kwargs):
        return self.write(*args, level="debug", **kwargs)

    def info(self, *args, **kwargs):
        return self.write(*args, level="info", **kwargs)

    def success(self, *args, **kwargs):
        return self.write(*args, level="success", **kwargs)

    def warning(self, *args, **kwargs):
        return self.write(*args, level="warning", **kwargs)

    def error(self, *args, **kwargs):
        return self.write(*args, level="error", **kwargs)

    def critical(self, *args, **kwargs):
        return self.write(*args, level="critical", **kwargs)

    # --- rendering -------------------------------------------------------------
    def _emit(self, args, level, color, timestamp):
        """One line, on the Tk thread: filter, format, mirror, print."""
        if _LEVEL_RANK.get(level, 20) < _LEVEL_RANK.get(self._min_level, 10):
            return
        line = self._format(args, level, timestamp)
        self._write_mirror(line)
        element = self._element
        if element.widget is None:
            return
        paint = self._colors.get(level, _LEVEL_COLORS.get(level))
        if color is not None:
            paint = color
        try:
            element.print(line, text_color=paint)
        except Exception:
            # the window went away mid-write (TclError); the mirror has it
            return
        self._trim()

    def _format(self, args, level, timestamp):
        if timestamp is False:
            stamp = ""
        else:
            pattern = self._timestamp if timestamp is None else str(timestamp)
            stamp = time.strftime(pattern) + " " if pattern else ""
        text = " ".join(str(arg) for arg in args)
        return f"{stamp}{level.upper():<{_LABEL_WIDTH}} {text}"

    def _write_mirror(self, line):
        if self._mirror is None:
            return
        with contextlib.suppress(Exception):
            self._mirror.write(line + "\n")
            self._mirror.flush()

    def _trim(self):
        """Keep the widget at ``max_lines`` by dropping the oldest lines."""
        if self._max_lines is None:
            return
        overflow = self._lines() - self._max_lines
        if overflow > 0:
            with contextlib.suppress(Exception):
                self._element.delete("1.0", f"{overflow + 1}.0")

    def _lines(self) -> int:
        try:
            return int(self._element.line_count)
        except Exception:
            return 0

    # --- cross thread plumbing -------------------------------------------------
    def _main_window(self):
        try:
            window = self._element.window
        except Exception:
            return None
        if window is None or window.was_closed:
            return None
        return window

    def _start_drain_timer(self):
        if self._timer is not None or self._drain_ms is None:
            return
        window = self._main_window()
        if window is None:
            return
        self._timer = window.every(self._drain_ms, self._drain)

    def _ensure_drain_timer(self):
        """Start the drain timer once the element's window is ready.

        Worker threads cannot touch tk directly, so the timer must already
        exist before the first cross-thread write; it is armed here (and at
        construction time when the window is finalized).
        """
        if self._timer is None:
            self._start_drain_timer()

    def _drain(self):
        """Move queued worker-thread lines into the widget (main thread)."""
        while True:
            try:
                payload = self._queue.get_nowait()
            except queue.Empty:
                return
            self._emit(*payload)

    def flush(self):
        """Write every queued line right now (call from the Tk thread)."""
        self._drain()
        return self

    # --- standard library bridge ------------------------------------------------
    def attach_logging(self, level=None, name=None):
        """Route the standard :mod:`logging` module into this log box::

            logger.attach_logging("INFO")          # root logger, INFO and up
            logger.attach_logging("DEBUG", "myapp")

        ``level`` sets both the handler filter and the target logger's own
        level (remembered, so :meth:`detach_logging` restores it) — without
        that second step Python would drop INFO records before they ever
        reach the handler.
        """
        target = logging.getLogger(name)
        for attached, _bridge, _previous in self._attachments:
            if attached is target:
                return self  # already bridged: never stack duplicate handlers
        bridge = _LoggingBridge(self)
        if level is not None:
            bridge.setLevel(_logging_level(level))
        previous = target.level
        if level is not None:
            target.setLevel(_logging_level(level))
        target.addHandler(bridge)
        self._attachments.append((target, bridge, previous))
        return self

    def detach_logging(self, name=None):
        """Remove every bridge this logger attached (optionally just ``name``)."""
        keep: List[Tuple[Any, Any, int]] = []
        for target, bridge, previous in self._attachments:
            if name is not None and target.name != name:
                keep.append((target, bridge, previous))
                continue
            target.removeHandler(bridge)
            target.setLevel(previous)
        self._attachments = keep
        return self

    # --- housekeeping -----------------------------------------------------------
    def clear(self):
        """Empty the widget; queued cross-thread lines still arrive after it."""
        with contextlib.suppress(Exception):
            self._element.clear()
        return self

    def close(self):
        """Detach the logging bridge, stop the timer, close an owned mirror."""
        self.detach_logging()
        if self._timer is not None:
            with contextlib.suppress(Exception):
                self._timer.cancel()
            self._timer = None
        if self._mirror_owned and self._mirror is not None:
            with contextlib.suppress(Exception):
                self._mirror.close()
            self._mirror = None
        return self

    @property
    def element(self):
        """The Multiline / Output element this logger renders into."""
        return self._element

    @property
    def lines(self) -> int:
        """Lines currently held by the widget."""
        return self._lines()

    @property
    def max_lines(self):
        """The ring buffer cap (``None`` = unlimited)."""
        return self._max_lines

    @property
    def level(self) -> str:
        """The minimum level that reaches the widget."""
        return self._min_level

    def __repr__(self):
        key = getattr(self._element, "key", None)
        return f"<Logger element={key!r} max_lines={self._max_lines}>"


def _logging_level(level) -> int:
    """Accept "warning" / "WARNING" / a number for the logging bridge."""
    if isinstance(level, int):
        return level
    name = str(level).upper()
    number = getattr(logging, name, None)
    if not isinstance(number, int):
        raise ValueError(f"unknown logging level: {level!r}")
    return number


class _LoggingBridge(logging.Handler):
    """``logging.Handler`` that renders records into a :class:`Logger`."""

    def __init__(self, logger: "Logger"):
        super().__init__()
        self._target = logger

    def emit(self, record):
        try:
            text = record.getMessage()
            if record.name not in ("root", ""):
                text = f"{record.name}: {text}"
            if record.exc_info:
                trace = record.exc_text
                if not trace:
                    trace = "".join(traceback.format_exception(*record.exc_info))
                text = f"{text}\n{trace.rstrip()}"
        except Exception:
            self.handleError(record)
            return
        self._target.write(text, level=_level_for_logging(record.levelno))


def find_log_element(key=None, window=None):
    """The Multiline / Output element a log line should be written to.

    With ``key`` the element with that key in the searched windows; without
    it the first Multiline / Output of the newest open window. Returns
    ``None`` when there is no log box yet (calling :func:`log` then is a
    no-op, not an error).
    """
    from .elements.widgets import Multiline
    from .window import Window

    candidates = (
        [window] if window is not None  # noqa: SLF001
        else list(reversed(Window._open_windows))  # noqa: SLF001  (internal registry)
    )
    for candidate in candidates:
        if candidate is None or candidate.was_closed:
            continue
        if key is not None:
            element = candidate.find_element(key)
            if isinstance(element, Multiline):
                return element
            continue
        for element in candidate.elements:
            if isinstance(element, Multiline):
                return element
    return None


def log(*args, key=None, level="info", color=None, window=None) -> bool:
    """Write one line into a window's log box — no logger object needed::

        ts.log("started")
        ts.log("sync failed", level="error")
        ts.log("tick", key="-LOG-")

    The line lands in the ``Output`` / ``Multiline`` element ``key``
    identifies, or in the first one of the newest open window. Returns
    ``True`` when a log box was found, ``False`` otherwise (so startup code
    may log before the window exists). Off-thread callers should keep a
    :class:`Logger` instead: this convenience writes straight to the widget.
    """
    element = find_log_element(key=key, window=window)
    if element is None:
        return False
    element.log(*args, level=level, color=color)
    return True
