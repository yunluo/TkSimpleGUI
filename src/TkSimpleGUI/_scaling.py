#!/usr/bin/env python3
"""DPI awareness and scaling plumbing for TkSimpleGUI.

Two scaling lines share one user-facing knob (``ts.settings.scaling``):

- **Fonts** scale automatically once the process is DPI aware. Every font in
  the package is specified in points (positive sizes), and Tk converts points
  to pixels through the interpreter-wide ``tk scaling`` factor, which
  :func:`apply_tk_scaling` sets from the live screen DPI times the user
  multiplier. Character-count widget widths (Entry/Button/Label) follow their
  fonts for free.
- **Pixel-domain layout** (grid padding, window margins/size/minsize, canvas
  sizes, ttk paddings) scales through :func:`scale_px`. The factor defaults
  to 1 so layout stays at 96-DPI logical pixels; setting
  ``ts.settings.scaling`` zooms fonts and layout together.
"""

from typing import Optional, Tuple
import tkinter as tk

from .settings import settings


# process-wide awareness attempt cache (the first call wins; the Win32 API
# refuses to change awareness after windows exist, so retrying is pointless)
_awareness_attempted = False
_awareness_result = False

# Tk's own DPI-derived ``tk scaling`` value, captured from the first root
# BEFORE we ever write the command (winfo_fpixels('1i') reads back through
# tk scaling itself, so re-reading it after a multiplier was applied would
# compound exponentially — capture once, then multiply the frozen base)
_native_tk_scaling: Optional[float] = None


def pixel_scale() -> float:
    """The user multiplier applied to pixel-domain layout values (default 1).

    ``ts.settings.scaling`` is either ``None`` (no extra zoom) or a positive
    factor such as 1.25 / 1.5 that zooms fonts and layout together.
    """
    multiplier = settings.scaling
    if multiplier is None:
        return 1.0
    return float(multiplier)


def scale_px(value: float) -> int:
    """Scale one pixel value by the user multiplier (never ``None``)."""
    return int(round(value * pixel_scale()))


def scale_opt(value: Optional[float]) -> Optional[int]:
    """scale_px for a possibly-``None`` size member (``None`` passes through)."""
    return None if value is None else scale_px(value)


def scale_pair(
    width: Optional[float],
    height: Optional[float],
) -> Tuple[Optional[int], Optional[int]]:
    """Scale a (width, height) pair; ``None`` members pass through."""
    return scale_opt(width), scale_opt(height)


def apply_tk_scaling(root: tk.Misc) -> float:
    """Set this interpreter's ``tk scaling`` from Tk's own DPI-derived base.

    Tk initializes ``tk scaling`` from the screen DPI when the process is DPI
    aware; the first root's pristine value is captured once and every later
    call re-applies ``base * settings.scaling`` so repeated window creation
    never compounds the multiplier. Call once per freshly created tk root,
    before any widget exists.
    """
    global _native_tk_scaling
    if _native_tk_scaling is None:
        _native_tk_scaling = float(root.tk.call("tk", "scaling"))
    value = _native_tk_scaling * pixel_scale()
    root.tk.call("tk", "scaling", value)
    return value


def ensure_dpi_awareness() -> bool:
    """Make the process DPI aware exactly once, before the first tk root.

    Off by default: set ``ts.settings.dpi_aware = True`` **before creating
    the first window** to enable it (DPI-aware Tk renders point-sized fonts
    at real pixels instead of blurry virtualization). The first call wins
    and later calls return the cached result (awareness cannot be changed
    once windows exist). Returns True when an awareness level is active.
    """
    global _awareness_attempted, _awareness_result
    if _awareness_attempted:
        return _awareness_result
    _awareness_attempted = True
    if not settings.dpi_aware:
        _awareness_result = False
        return _awareness_result
    from .utils import set_dpi_awareness

    # system awareness on purpose: Tk 8.6 is not per-monitor aware, so the
    # per-monitor level only changes message delivery without buying
    # anything; system level still gives Tk the true primary-screen DPI
    _awareness_result = bool(set_dpi_awareness(prefer_per_monitor=False))
    return _awareness_result
