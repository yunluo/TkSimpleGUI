# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""TkSimpleGUI theming.

All theme state is encapsulated in :class:`ThemeManager`. By default the
manager is in "native" mode: no colors are overridden and ttk widgets use the
system's native look (Windows Vista style, macOS Aqua, ...). Applying a named
theme from :data:`THEMES` switches to TkSimpleGUI colors.
"""

from typing import Any, Optional, Sequence
import contextlib
import time
import tkinter as tk
from tkinter import ttk

from . import constants as C
from ._scaling import apply_tk_scaling, ensure_dpi_awareness, scale_px
from ._theme_data import THEMES
from .constants import Color, ElementKey


def _is_system_default(value: Any):
    """True when ``value`` is the ``COLOR_SYSTEM_DEFAULT`` sentinel.

    Several built-in themes encode "use the platform default color" as the
    literal string ``COLOR_SYSTEM_DEFAULT`` (= ``"1234567890"``). Those
    values must be filtered out before passing them to Tk, otherwise the
    user gets ``TclError: unknown color name "1234567890"``.
    """
    return value is None or value == C.COLOR_SYSTEM_DEFAULT


# --- small hex color helpers (module level, used by the ttk skin) --------------
def _parse_hex(color: Optional[Color]):
    """``#rrggbb`` -> ``(r, g, b)``, or ``None`` for named/invalid colors."""
    if not color:
        return None
    try:
        value = color.lstrip("#")
        if len(value) != 6:
            return None
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    except (AttributeError, TypeError, ValueError):
        return None


def _blend(color: Optional[Color], other: Any, ratio: float):
    """Mix ``color`` toward ``other`` by ``ratio`` (0..1). Non-hex passthrough."""
    base, target = _parse_hex(color), _parse_hex(other)
    if base is None or target is None:
        return color
    mixed = tuple(round(b + (t - b) * ratio) for b, t in zip(base, target))
    return "#{:02x}{:02x}{:02x}".format(*mixed)


def _luminance(color: Optional[Color]):
    """Perceived brightness 0..1 (unknown colors count as mid gray)."""
    rgb = _parse_hex(color)
    if rgb is None:
        return 0.5
    return (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255.0


def contrast_on(color: Optional[Color]):
    """Black or white text color — whichever reads better on ``color``."""
    return "#ffffff" if _luminance(color) < 0.55 else "#1e2228"


def native_widget_colors(widget_class: Any, master: tk.Misc, options: Sequence[Any]):
    """Sample platform-default option values from a throwaway widget.

    Classic tk widgets reject ``""`` as a color, so the only reliable way
    to undo theme colors is to copy the defaults from a fresh instance of
    the same class. Returns ``{option: value}``.
    """
    probe = widget_class(master)
    try:
        return {option: str(probe.cget(option)) for option in options}
    finally:
        probe.destroy()



_THEME_KEY_ALIASES = {
    "BACKGROUND": "BACKGROUND",
    "TEXT": "TEXT",
    "INPUT": "INPUT",
    "TEXT_INPUT": "TEXT_INPUT",
    "BUTTON": "BUTTON",
    "PROGRESS": "PROGRESS",
    "SCROLL": "SCROLL",
    "BORDER": "BORDER",
    "SLIDER_DEPTH": "SLIDER_DEPTH",
    "COLOR_LIST": "COLOR_LIST",
}


class ThemeManager:
    """Encapsulated look and feel state.

    ``name is None`` means *native*: no colors are overridden and ttk widgets
    keep the system's default theme. ``theme_version`` increments on every
    mutation so live windows can detect "my palette is stale" and re-apply
    their colors (see :meth:`Window.update_theme`).
    """

    __slots__ = ("_name", "_style_cache", "_theme_version", "_native_engine",
                 "_transition_from", "_transition_start", "_transition_ms")

    # frame interval of the theme-switch transition loop (milliseconds)
    _FRAME_MS = 20

    def __init__(self):
        self._name = None
        self._style_cache = {}
        self._theme_version = 0
        self._native_engine = None
        self._transition_from: Optional[Any] = None
        self._transition_start = 0.0
        self._transition_ms = 1.0

    @property
    def theme_version(self):
        """Monotonic counter bumped whenever theme colors change."""
        return self._theme_version

    # --- name handling -----------------------------------------------------
    @property
    def name(self):
        """Current theme name, or ``None`` for the native system look."""
        return self._name

    @property
    def is_native(self):
        """True when the current theme defers to the platform's native look.

        This covers both "no theme applied" (``name is None``) and the
        explicit ``System`` theme -- both leave every color override at
        the ``COLOR_SYSTEM_DEFAULT`` sentinel, so the platform's defaults
        show through.
        """
        return self._name is None or self._name == "System"

    def apply(self, name: str, transition_ms: int = 0):
        """Apply a theme by name (case insensitive). Returns the canonical name.

        With ``transition_ms > 0`` the switch is animated: the previous
        theme's colors ease-blend into the new ones over the given
        duration while every open window repaints per frame. Both the old
        and the new look must be non-native for a transition to run —
        anything else (native look at either end, no live windows) snaps.
        """
        if name is None:
            self._name = None
            self._transition_from = None
            return None
        if not isinstance(name, str):
            raise TypeError("theme name must be a string or None")
        if name in THEMES:
            canonical = name
        else:
            canonical = None
            for candidate in THEMES:
                if candidate.lower() == name.lower():
                    canonical = candidate
                    break
            if canonical is None:
                raise ValueError(
                    f"Invalid theme name: {name!r}. Use theme_list() "
                    "for the available themes."
                )
        previous = None
        if transition_ms and transition_ms > 0 and self._name is not None \
                and not self.is_native:
            previous = dict(self._entry())
        self._name = canonical
        self._theme_version += 1
        if previous is not None and not self.is_native:
            self._start_transition(previous, int(transition_ms))
        else:
            self._transition_from = None
        return canonical

    def add_new(self, name: str, colors: Any):
        """Register a new theme definition (dict of color entries)."""
        if not isinstance(name, str) or not name:
            raise ValueError("theme name must be a non-empty string")
        THEMES[name] = dict(colors)
        self._theme_version += 1
        return name

    # --- raw entry ---------------------------------------------------------
    def _entry(self):
        if self._name is None:
            return {}
        return THEMES.get(self._name, {})

    def _get(self, key: ElementKey, default: Any = None):
        return self._entry().get(key, default)

    # --- theme-switch transition -------------------------------------------
    def _start_transition(self, previous: Any, ms: int):
        """Begin blending ``previous`` (old theme entry) into the current
        theme over ``ms`` milliseconds."""
        self._transition_from = previous
        self._transition_start = time.time()
        self._transition_ms = max(int(ms), 50) / 1000.0
        self._schedule_tick()

    def _schedule_tick(self):
        """Queue the next animation frame on the hidden master root."""
        from .window.window import Window

        root = Window._main_root
        if root is None:
            self._transition_from = None  # nothing live to animate on
            return
        try:
            root.after(self._FRAME_MS, self._tick)
        except tk.TclError:
            self._transition_from = None

    def _tick(self):
        """One animation frame: repaint every window with the blended
        palette; the final frame paints the exact new colors."""
        if self._transition_from is None:
            return
        finished = time.time() - self._transition_start >= self._transition_ms
        self._repaint_windows()
        if finished:
            self._transition_from = None
        else:
            self._schedule_tick()

    def _repaint_windows(self):
        from .window.window import Window

        for window in list(Window._open_windows):
            if window._parent is None:  # update_theme recurses into children
                window.update_theme()

    def _progress(self):
        """Eased transition progress 0..1 (ease-out cubic)."""
        progress = min(
            max((time.time() - self._transition_start) / self._transition_ms, 0.0),
            1.0)
        return 1.0 - (1.0 - progress) ** 3

    def _blend_pair(self, old: Any, new: Any):
        """Blend one color from the old theme into the current value; a
        missing or native endpoint snaps to ``new`` untouched."""
        if self._transition_from is None or _is_system_default(new) \
                or old is None or _is_system_default(old):
            return new
        return _blend(old, new, self._progress())

    def _transitioned(self, key: ElementKey, value: Any):
        """A leaf theme color while a transition is active: the eased mix
        of the previous entry's value into the current one."""
        if self._transition_from is None:
            return value
        old = self._transition_from.get(key)
        if isinstance(value, (tuple, list)):
            old_values = old if isinstance(old, (tuple, list)) else ()
            blended = [
                self._blend_pair(
                    old_values[i] if i < len(old_values) else None, item)
                for i, item in enumerate(value)
            ]
            return type(value)(blended)
        return self._blend_pair(old, value)

    # --- color properties --------------------------------------------------
    @property
    def background_color(self):
        """Window background color, or None for native."""
        return self._transitioned("BACKGROUND", self._get("BACKGROUND"))

    @property
    def text_color(self):
        return self._transitioned("TEXT", self._get("TEXT"))

    @property
    def input_background_color(self):
        return self._transitioned("INPUT", self._get("INPUT"))

    @property
    def input_text_color(self):
        return self._transitioned("TEXT_INPUT", self._get("TEXT_INPUT"))

    @property
    def button_colors(self):
        """(text_color, background_color) tuple for buttons, or None."""
        value = self._transitioned("BUTTON", self._get("BUTTON"))
        if value is None:
            return None
        if isinstance(value, str):  # some entries store a single color
            return (None, value)
        return value

    @property
    def progress_bar_colors(self):
        value = self._transitioned("PROGRESS", self._get("PROGRESS"))
        if value is None:
            return None
        if isinstance(value, str):
            return (value, None)
        return value

    @property
    def slider_color(self):
        return self._transitioned("SCROLL", self._get("SCROLL"))

    @property
    def border_width(self):
        return self._get("BORDER", 1)

    @property
    def slider_depth(self):
        return self._get("SLIDER_DEPTH", 4)

    @property
    def color_list(self):
        return self._transitioned("COLOR_LIST", self._get("COLOR_LIST", []))

    def accent_color(self):
        """The theme's accent hue — selections, slider handles, focus rings.

        Falls back through COLOR_LIST[1] -> button background -> progress
        bar color. ``None`` for the native look.
        """
        if self.is_native:
            return None
        colors = self.color_list
        if len(colors) > 1 and _parse_hex(colors[1]) is not None:
            return colors[1]
        button = self.button_colors
        if button is not None and _parse_hex(button[1] or "") is not None:
            return button[1]
        progress = self.progress_bar_colors
        if progress is not None and _parse_hex(progress[0] or "") is not None:
            return progress[0]
        return None

    def muted_color(self):
        """A dimmed text color (secondary labels, inactive tabs), or None."""
        if self.is_native:
            return None
        bg, fg = self.background_color, self.text_color
        if _is_system_default(bg) or _is_system_default(fg):
            return None
        return _blend(fg, bg, 0.45)

    def tooltip_colors(self):
        """tk kwargs for hover tooltips; ``{}`` keeps the platform default."""
        bg, fg = self.background_color, self.text_color
        if _is_system_default(bg) or _is_system_default(fg):
            return {}
        return {"background": _blend(bg, fg, 0.12), "foreground": fg}

    # --- tk kwargs helpers --------------------------------------------------
    def effective_background(self, override: Any = None):
        """A concrete background color for tk.Frame-like widgets.

        ``override`` (an explicit per-widget color) wins; otherwise the
        theme background is used. Returns ``None`` when the result would be
        the ``COLOR_SYSTEM_DEFAULT`` sentinel (native look — leave the
        platform default in place).
        """
        bg = override or self.background_color
        return None if _is_system_default(bg) else bg

    def window_kwargs(self):
        """tk kwargs for the window background (empty dict when native)."""
        if self.is_native or _is_system_default(self.background_color):
            return {}
        return {"background": self.background_color}

    def text_kwargs(self, color: Optional[Color] = None, background_color: Optional[Color] = None):
        """tk kwargs for plain text-ish widgets."""
        kwargs = {}
        bg = background_color if background_color is not None else self.background_color
        fg = color if color is not None else self.text_color
        if not _is_system_default(bg):
            kwargs["background"] = bg
        if not _is_system_default(fg):
            kwargs["foreground"] = fg
        return kwargs

    def input_kwargs(
        self,
        text_color: Optional[Color] = None,
        background_color: Optional[Color] = None,
        include_caret: bool = True):
        """tk kwargs for input widgets.

        ``include_caret=False`` drops ``insertbackground`` for widgets that
        do not support a text caret (e.g. tk.Listbox).
        """
        kwargs = {}
        bg = (
            background_color
            if background_color is not None
            else self.input_background_color
        )
        fg = text_color if text_color is not None else self.input_text_color
        if not _is_system_default(bg):
            kwargs["background"] = bg
            if not _is_system_default(fg) and include_caret:
                kwargs["insertbackground"] = fg
        if not _is_system_default(fg):
            kwargs["foreground"] = fg
            if include_caret:
                kwargs["insertbackground"] = fg
        accent = self.accent_color()
        if accent is not None and kwargs.get("background") is not None:
            kwargs["selectbackground"] = accent
            kwargs["selectforeground"] = contrast_on(accent)
        return kwargs

    def button_kwargs(self, button_color: Optional[Color] = None):
        """tk kwargs for classic (tk) buttons."""
        colors = button_color if button_color is not None else self.button_colors
        kwargs = {}
        if colors is not None:
            fg, bg = colors
            if not _is_system_default(fg):
                kwargs["foreground"] = fg
            if not _is_system_default(bg):
                kwargs["background"] = bg
            if not _is_system_default(fg) or not _is_system_default(bg):
                kwargs["activeforeground"] = fg
                kwargs["activebackground"] = bg
        return kwargs

    # --- ttk styling ---------------------------------------------------------
    def ttk_widget_style(self, master: tk.Misc, base: Any, **options: Any):
        """Return a ttk style name honouring per-widget option overrides.

        ``base`` is a ttk style class such as ``"TEntry"``. When every option
        is ``None`` the plain base is returned (no derived style is created).
        Derived styles are cached so widgets asking for the same combination
        share one style.
        """
        effective = {
            key: value for key, value in options.items() if value is not None
        }
        if not effective:
            return base
        style = ttk.Style(master)
        cache_key = (base,) + tuple(sorted(effective.items()))
        name = self._style_cache.get(cache_key)
        if name is None:
            name = f"PSG4_{len(self._style_cache)}.{base}"
            self._style_cache[cache_key] = name
            style.configure(name, **effective)
        return name

    def configure_ttk(self, style: "ttk.Style"):
        """Apply the current theme to a ``ttk.Style``.

        Under the native look this *restores*: the ttk engine returns to the
        platform's own theme so widgets keep the system appearance even
        after a themed session. Under a named theme the ``clam`` engine is
        skinned with the palette — every widget class gets configured and
        given state maps (hover / pressed / disabled / selected / focus) so
        the look stays alive instead of being a flat color swap.
        """
        if self.is_native:
            if self._native_engine is not None:
                with contextlib.suppress(Exception):
                    if style.theme_use() != self._native_engine:
                        style.theme_use(self._native_engine)
            return
        try:
            if self._native_engine is None:
                self._native_engine = style.theme_use()
            if style.theme_use() != "clam":
                style.theme_use("clam")
        except Exception:
            pass

        bg = self.background_color or "#e8e8e8"
        fg = self.text_color or "#000000"
        input_bg = self.input_background_color or bg
        input_fg = self.input_text_color or fg
        button = self.button_colors
        if button is None:
            button = (fg, _blend(bg, fg, 0.18))
        btn_fg = button[0] or fg
        btn_bg = button[1] or bg
        accent = self.accent_color() or btn_bg
        accent_fg = contrast_on(accent)

        # one shared set of derived state colors keeps the look coherent
        border = _blend(bg, fg, 0.18)
        muted = _blend(fg, bg, 0.45)
        disabled_bg = _blend(btn_bg, bg, 0.72)
        disabled_fg = _blend(btn_fg, bg, 0.55)
        hover = _blend(btn_bg, "#ffffff", 0.12)
        pressed = _blend(btn_bg, "#000000", 0.16)
        disabled_field = _blend(input_bg, bg, 0.45)

        style.configure(
            ".", background=bg, foreground=fg, bordercolor=border,
            lightcolor=border, darkcolor=border, troughcolor=input_bg,
            focuscolor=accent, selectbackground=accent,
            selectforeground=accent_fg, insertcolor=input_fg,
            borderwidth=self.border_width,
        )
        style.configure("TFrame", background=bg)
        style.configure("Tab.TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg)

        # --- buttons: flat-ish surfaces with depth, quiet disabled state ----
        button_config = {
            "background": btn_bg, "foreground": btn_fg,
            "bordercolor": _blend(btn_bg, "#000000", 0.25),
            "lightcolor": _blend(btn_bg, "#ffffff", 0.08),
            "darkcolor": _blend(btn_bg, "#000000", 0.20),
        }
        button_map = {
            "background": [("disabled", disabled_bg), ("pressed", pressed),
                           ("active", hover)],
            "foreground": [("disabled", disabled_fg)],
        }
        for base in ("TButton", "TMenubutton"):
            style.configure(base, **button_config)
            style.map(base, **button_map)  # ty: ignore[no-matching-overload]  dynamic tk query

        # --- entries: quiet border, accent focus ring, dim disabled field ---
        entry_map = {
            "fieldbackground": [("disabled", disabled_field), ("readonly", input_bg)],
            "foreground": [("disabled", muted)],
            "bordercolor": [("focus", accent)],
            "lightcolor": [("focus", accent)],
            "darkcolor": [("focus", accent)],
        }
        for base in ("TEntry", "TSpinbox", "TCombobox"):
            style.configure(
                base, fieldbackground=input_bg, foreground=input_fg,
                bordercolor=border, lightcolor=border, darkcolor=border,
                insertcolor=input_fg, selectbackground=accent,
                selectforeground=accent_fg,
            )
            style.map(base, **entry_map)  # ty: ignore[no-matching-overload]  dynamic tk query
        for base in ("TSpinbox", "TCombobox"):
            style.configure(base, arrowcolor=input_fg)
            style.map(base, arrowcolor=[("disabled", muted)])

        # the combobox dropdown list is a classic tk.Listbox: option database
        master = style.master
        for option, value in (
            ("*TCombobox*Listbox.background", input_bg),
            ("*TCombobox*Listbox.foreground", input_fg),
            ("*TCombobox*Listbox.selectBackground", accent),
            ("*TCombobox*Listbox.selectForeground", accent_fg),
        ):
            master.option_add(option, value)

        # --- check/radio: themed indicator surface + accent check/dot -------
        indicator_surface = _blend(input_bg, bg, 0.25)
        for base in ("TCheckbutton", "TRadiobutton"):
            style.configure(
                base, background=bg, foreground=fg,
                indicatorbackground=indicator_surface,
                indicatorforeground=accent,
                upperbordercolor=border, lowerbordercolor=border,
            )
            style.map(
                base,
                indicatorbackground=[
                    ("disabled", _blend(indicator_surface, bg, 0.5)),
                    ("pressed", _blend(indicator_surface, fg, 0.22)),
                ],
                foreground=[("disabled", muted)],
            )

        # --- scale: accent handle on a flat trough ---------------------------
        scroll = self.slider_color
        trough = (
            scroll
            if not _is_system_default(scroll)
            else _blend(input_bg, bg, 0.35)
        )
        for base in ("Horizontal.TScale", "Vertical.TScale"):
            style.configure(
                base, troughcolor=trough, background=accent,
                bordercolor=trough, lightcolor=trough, darkcolor=trough,
                gripcount=0,
            )
            style.map(
                base,
                background=[("disabled", _blend(accent, bg, 0.5)),
                            ("active", _blend(accent, "#ffffff", 0.15))],
            )

        # --- progress: flat accent bar on a quiet trough ---------------------
        progress = self.progress_bar_colors
        bar_color = progress[0] if progress and progress[0] else accent
        trough_color = (
            progress[1] if progress and progress[1]
            else _blend(input_bg, bg, 0.35)
        )
        for base in ("Horizontal.TProgressbar", "Vertical.TProgressbar"):
            style.configure(
                base, background=bar_color, troughcolor=trough_color,
                bordercolor=trough_color, lightcolor=bar_color,
                darkcolor=bar_color,
            )

        # --- notebook: raised selected tab, dimmed idle tabs ------------------
        style.configure(
            "TNotebook", background=bg, bordercolor=border, lightcolor=bg,
            darkcolor=bg, tabmargins=(scale_px(6), scale_px(4), scale_px(6), 0),
        )
        style.configure(
            "TNotebook.Tab", background=bg, foreground=muted,
            bordercolor=border, lightcolor=border, darkcolor=border,
            padding=(scale_px(10), scale_px(5)),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", input_bg)],
            foreground=[("selected", fg),
                        ("disabled", _blend(muted, bg, 0.4))],
            lightcolor=[("selected", input_bg)],
            darkcolor=[("selected", input_bg)],
        )

        # --- tree/table -------------------------------------------------------
        style.configure(
            "Treeview", background=input_bg, fieldbackground=input_bg,
            foreground=input_fg, bordercolor=border, lightcolor=border,
            darkcolor=border,
        )
        style.map(
            "Treeview",
            background=[("selected", accent)],
            foreground=[("selected", accent_fg)],
        )
        style.configure(
            "Treeview.Heading", background=bg, foreground=_blend(fg, bg, 0.25),
            bordercolor=border, lightcolor=border, darkcolor=border,
            relief="flat", padding=(scale_px(6), scale_px(4)),
        )
        style.map("Treeview.Heading", foreground=[("active", fg)])

        # --- containers ---------------------------------------------------------
        style.configure(
            "TLabelframe", background=bg, bordercolor=border,
            lightcolor=border, darkcolor=border,
        )
        style.configure("TLabelframe.Label", background=bg, foreground=fg)
        style.configure("TSeparator", background=border)
        style.configure("TPanedwindow", background=bg)
        style.configure("Sash", sashthickness=scale_px(6), gripcount=0, background=border)
        style.configure("TSizegrip", background=bg)

        # per-widget derived styles (explicit user colors) need the same
        # state maps, otherwise hover/disabled fall back to engine defaults
        for cache_key, name in self._style_cache.items():
            base = cache_key[0]
            if base in ("TButton", "TMenubutton"):
                style.map(name, **button_map)  # ty: ignore[no-matching-overload]  dynamic tk query
            elif base in ("TEntry", "TSpinbox", "TCombobox"):
                style.map(
                    name,
                    fieldbackground=[("disabled", disabled_field)],
                    foreground=[("disabled", muted)],
                    bordercolor=[("focus", accent)],
                    lightcolor=[("focus", accent)],
                    darkcolor=[("focus", accent)],
                )
            elif base in ("TCheckbutton", "TRadiobutton"):
                style.map(name, foreground=[("disabled", muted)])


theme_manager = ThemeManager()


_UNSET = object()


def theme(name: Any = _UNSET, transition_ms: int = 0):
    """Get or set the current theme.

    ``theme()`` returns the current theme name (``None`` = system native).
    ``theme("DarkBlue3")`` applies a theme and returns its canonical name.
    ``theme(None)`` explicitly resets to the native system look and returns None.
    ``theme("DarkBlue3", transition_ms=250)`` morphs the colors smoothly:
    the old palette eases into the new one over the given duration while
    every open window repaints per frame (needs a non-native look at both
    ends and at least one live window, otherwise it snaps).
    """
    if name is _UNSET:
        return theme_manager.name
    return theme_manager.apply(name, transition_ms=transition_ms)


def theme_list():
    """Sorted list of available theme names."""
    return sorted(THEMES)


def theme_background_color(color: Optional[Color] = None):
    """Get or set the current theme's window background color."""
    if color is not None:
        theme_manager._entry()["BACKGROUND"] = color  # noqa: SLF001
        theme_manager._theme_version += 1  # noqa: SLF001
    return theme_manager.background_color


def theme_text_color(color: Optional[Color] = None):
    """Get or set the current theme's text color."""
    if color is not None:
        theme_manager._entry()["TEXT"] = color  # noqa: SLF001
        theme_manager._theme_version += 1  # noqa: SLF001
    return theme_manager.text_color


def theme_button_color(color: Optional[Color] = None):
    """Get or set the current theme's button (text, background) colors."""
    if color is not None:
        theme_manager._entry()["BUTTON"] = color  # noqa: SLF001
        theme_manager._theme_version += 1  # noqa: SLF001
    return theme_manager.button_colors


def theme_input_background_color(color: Optional[Color] = None):
    """Get or set the current theme's input background color."""
    if color is not None:
        theme_manager._entry()["INPUT"] = color  # noqa: SLF001
        theme_manager._theme_version += 1  # noqa: SLF001
    return theme_manager.input_background_color


def theme_input_text_color(color: Optional[Color] = None):
    """Get or set the current theme's input text color."""
    if color is not None:
        theme_manager._entry()["TEXT_INPUT"] = color  # noqa: SLF001
        theme_manager._theme_version += 1  # noqa: SLF001
    return theme_manager.input_text_color


def theme_progress_bar_color(
    bar_color: Optional[Color] = None,
    background_color: Optional[Color] = None):
    """Get or set the current theme's progress bar (bar, trough) colors."""
    if bar_color is not None or background_color is not None:
        current = theme_manager.progress_bar_colors or (None, None)
        new_bar = bar_color if bar_color is not None else current[0]
        new_bg = background_color if background_color is not None else current[1]
        theme_manager._entry()["PROGRESS"] = (new_bar, new_bg)  # noqa: SLF001
        theme_manager._theme_version += 1  # noqa: SLF001
    return theme_manager.progress_bar_colors


def theme_slider_color(color: Optional[Color] = None):
    """Get or set the current theme's slider color."""
    if color is not None:
        theme_manager._entry()["SCROLL"] = color  # noqa: SLF001
        theme_manager._theme_version += 1  # noqa: SLF001
    return theme_manager.slider_color


def theme_border_width(width: Optional[int] = None):
    """Get or set the current theme's border width."""
    if width is not None:
        theme_manager._entry()["BORDER"] = width  # noqa: SLF001
        theme_manager._theme_version += 1  # noqa: SLF001
    return theme_manager.border_width


def theme_add(name: str, colors: Any):
    """Register a new theme; returns the canonical name."""
    return theme_manager.add_new(name, colors)


# --- ttk engine themes (clam/vista/aqua/alt/default…) -------------------------
def ttk_themes():
    """Names of the underlying ttk engine themes available on this platform."""
    import tkinter as tk

    root = None
    from .window import Window

    for window in Window._open_windows:
        if window._root_alive():
            root = window.tk_root
            break
    temporary = root is None
    if temporary:
        ensure_dpi_awareness()
        root = tk.Tk()
        apply_tk_scaling(root)
        root.withdraw()
    try:
        return sorted(ttk.Style(root).theme_names())
    finally:
        if temporary:
            root.destroy()


def ttk_theme(name: Optional[str] = None):
    """Get or set the ttk engine theme on every open window.

    Independent from the 160 TkSimpleGUI color themes: this selects the
    widget *engine* look (Windows: "vista"/"xpnative"; Linux: "clam"/"alt";
    macOS: "aqua"). Without arguments returns the current engine theme.
    """
    if name is None:
        from .window import Window

        for window in Window._open_windows:
            if window._root_alive():
                return ttk.Style(window.tk_root).theme_use()
        return None
    from .window import Window

    applied = None
    for window in Window._open_windows:
        if window._root_alive():
            try:
                ttk.Style(window.tk_root).theme_use(name)
                applied = name
            except tk.TclError:
                pass
    if applied is None:
        raise ValueError(
            f"Unknown ttk theme {name!r} (or no open window); "
            f"available: {ttk_themes()}"
        )
    return applied
