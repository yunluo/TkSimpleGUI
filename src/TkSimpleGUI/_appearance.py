#!/usr/bin/env python3
"""System light/dark preference reading and theme following.

``system_prefers_dark`` reads the Windows personalization registry value
that darkdetect-style libraries poll; ``start_follow`` runs a 2-second
``after`` poll chain on the hidden master root and switches the theme
between ``settings.theme_light`` / ``settings.theme_dark`` when the
system preference flips (CustomTkinter's AppearanceModeTracker idea,
without the 30ms aggression).
"""

import contextlib
import logging
import sys
from typing import Optional

from .settings import settings

_appearance_logger = logging.getLogger("TkSimpleGUI.appearance")

_FOLLOW_INTERVAL_MS = 2000

# module poll state (None = not following / no reading yet)
_job: Optional[str] = None
_last_prefers: Optional[bool] = None


def system_prefers_dark() -> Optional[bool]:
    """True when Windows personalization is in dark mode for apps.

    None when the answer is unknown (not Windows, or the registry value
    is missing — e.g. Server cores and stripped-down installs).
    """
    if not sys.platform.startswith("win"):
        return None
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        ) as key:
            value, _kind = winreg.QueryValueEx(key, "AppsUseLightTheme")
    except OSError:
        return None
    # the flag is "1 = light mode"; anything else counts as dark
    return not bool(value)


def start_follow() -> bool:
    """Start following the system light/dark preference (idempotent).

    Runs a 2-second ``after`` chain on the hidden master root, so the
    check fires whenever the application pumps events. When the system
    preference flips, the theme switches to ``settings.theme_dark`` /
    ``settings.theme_light``. Does nothing when already following or on
    systems without a readable preference. Returns True when following.
    """
    global _job, _last_prefers
    if _job is not None:
        return True
    if system_prefers_dark() is None:
        return False
    _last_prefers = None
    _job = _schedule_tick()
    return _job is not None


def stop_follow() -> None:
    """Stop the follow poll (harmless when not running)."""
    global _job
    if _job is not None:
        from .window.window import Window

        if Window._main_root is not None and Window._main_root.winfo_exists():
            with contextlib.suppress(Exception):
                Window._main_root.after_cancel(_job)
        _job = None


def poll_once() -> Optional[bool]:
    """One follow check; switches the theme when it disagrees with the system.

    The first poll aligns the theme to the current system preference
    (so ``theme_follow_system`` snaps to the OS look right after start),
    later polls switch only on a flip. Returns the current system
    preference, or None when unknown. Exposed for tests; ``start_follow``
    calls it on a timer.
    """
    global _last_prefers
    prefers = system_prefers_dark()
    if prefers is None:
        return None
    if _last_prefers is None or prefers != _last_prefers:
        target = settings.theme_dark if prefers else settings.theme_light
        _appearance_logger.info(
            "system theme is %s; following with %r",
            "dark" if prefers else "light", target,
        )
        from ._theming import theme

        theme(target)
    _last_prefers = prefers
    return prefers


def _schedule_tick() -> Optional[str]:
    """Arm one poll tick on the master root; None when no root exists."""
    from .window.window import Window

    root = Window._main_root
    if root is None or not root.winfo_exists():
        return None
    if not Window._open_windows:
        return None  # nothing to repaint while every window is closed
    return root.after(_FOLLOW_INTERVAL_MS, _tick)


def _tick() -> None:
    """One poll beat: check, then re-arm (stops when windows are gone)."""
    global _job
    _job = None
    poll_once()
    _job = _schedule_tick()


def _reset_for_tests() -> None:
    """Reset module poll state (tests only)."""
    stop_follow()
    global _last_prefers
    _last_prefers = None
