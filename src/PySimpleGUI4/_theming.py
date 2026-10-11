#!/usr/bin/env python3
"""PySimpleGUI4 theming.

All theme state is encapsulated in :class:`ThemeManager`. By default the
manager is in "native" mode: no colors are overridden and ttk widgets use the
system's native look (Windows Vista style, macOS Aqua, ...). Applying a named
theme from :data:`LOOK_AND_FEEL_TABLE` switches to PySimpleGUI colors.
"""

import tkinter as tk
from tkinter import ttk

from ._theme_data import LOOK_AND_FEEL_TABLE



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


class ThemeManager(object):
    """Encapsulated look and feel state.

    ``name is None`` means *native*: no colors are overridden and ttk widgets
    keep the system's default theme.
    """

    __slots__ = ("_name", "_style_cache")

    def __init__(self):
        self._name = None
        self._style_cache = {}

    # --- name handling -----------------------------------------------------
    @property
    def name(self):
        """Current theme name, or ``None`` for the native system look."""
        return self._name

    @property
    def is_native(self):
        """True when no custom theme has been applied."""
        return self._name is None

    def apply(self, name):
        """Apply a theme by name (case insensitive). Returns the canonical name."""
        if name is None:
            self._name = None
            return None
        if not isinstance(name, str):
            raise TypeError("theme name must be a string or None")
        if name in LOOK_AND_FEEL_TABLE:
            canonical = name
        else:
            canonical = None
            for candidate in LOOK_AND_FEEL_TABLE:
                if candidate.lower() == name.lower():
                    canonical = candidate
                    break
            if canonical is None:
                raise ValueError(
                    f"Invalid theme name: {name!r}. Use list_of_look_and_feel_values() "
                    "for the available themes."
                )
        self._name = canonical
        return canonical

    def add_new(self, name, colors):
        """Register a new theme definition (dict of color entries)."""
        if not isinstance(name, str) or not name:
            raise ValueError("theme name must be a non-empty string")
        LOOK_AND_FEEL_TABLE[name] = dict(colors)
        return name

    # --- raw entry ---------------------------------------------------------
    def _entry(self):
        if self._name is None:
            return {}
        return LOOK_AND_FEEL_TABLE.get(self._name, {})

    def _get(self, key, default=None):
        return self._entry().get(key, default)

    # --- color properties --------------------------------------------------
    @property
    def background_color(self):
        """Window background color, or None for native."""
        return self._get("BACKGROUND")

    @property
    def text_color(self):
        return self._get("TEXT")

    @property
    def input_background_color(self):
        return self._get("INPUT")

    @property
    def input_text_color(self):
        return self._get("TEXT_INPUT")

    @property
    def button_colors(self):
        """(text_color, background_color) tuple for buttons, or None."""
        value = self._get("BUTTON")
        if value is None:
            return None
        if isinstance(value, str):  # some entries store a single color
            return (None, value)
        return value

    @property
    def progress_bar_colors(self):
        value = self._get("PROGRESS")
        if value is None:
            return None
        if isinstance(value, str):
            return (value, None)
        return value

    @property
    def slider_color(self):
        return self._get("SCROLL")

    @property
    def border_width(self):
        return self._get("BORDER", 1)

    @property
    def slider_depth(self):
        return self._get("SLIDER_DEPTH", 4)

    @property
    def color_list(self):
        return self._get("COLOR_LIST", [])

    # --- tk kwargs helpers --------------------------------------------------
    def window_kwargs(self):
        """tk kwargs for the window background (empty dict when native)."""
        if self.is_native or self.background_color is None:
            return {}
        return {"background": self.background_color}

    def text_kwargs(self, color=None, background_color=None):
        """tk kwargs for plain text-ish widgets."""
        kwargs = {}
        bg = background_color if background_color is not None else self.background_color
        fg = color if color is not None else self.text_color
        if bg is not None:
            kwargs["background"] = bg
        if fg is not None:
            kwargs["foreground"] = fg
        return kwargs

    def input_kwargs(self, text_color=None, background_color=None):
        """tk kwargs for input widgets."""
        kwargs = {}
        bg = (
            background_color
            if background_color is not None
            else self.input_background_color
        )
        fg = text_color if text_color is not None else self.input_text_color
        if bg is not None:
            kwargs["background"] = bg
            kwargs["insertbackground"] = fg if fg is not None else bg
        if fg is not None:
            kwargs["foreground"] = fg
            kwargs["insertbackground"] = fg
        return kwargs

    def button_kwargs(self, button_color=None):
        """tk kwargs for classic (tk) buttons."""
        colors = button_color if button_color is not None else self.button_colors
        kwargs = {}
        if colors is not None:
            fg, bg = colors
            if fg is not None:
                kwargs["foreground"] = fg
            if bg is not None:
                kwargs["background"] = bg
            if fg is not None or bg is not None:
                kwargs["activeforeground"] = fg
                kwargs["activebackground"] = bg
        return kwargs

    # --- ttk styling ---------------------------------------------------------
    def ttk_widget_style(self, master, base, **options):
        """Return a ttk style name honouring per-widget option overrides.

        ``base`` is a ttk style class such as ``"TEntry"``. When every option
        is ``None`` the plain base is returned (no derived style is created).
        Derived styles are cached so widgets asking for the same combination
        share one style.
        """
        effective = dict(
            (key, value) for key, value in options.items() if value is not None
        )
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

    def configure_ttk(self, style):
        """Apply the current theme to a ``ttk.Style`` (no-op when native)."""
        if self.is_native:
            return
        try:
            style.theme_use("clam")
        except Exception:
            pass
        bg = self.background_color or "#e8e8e8"
        fg = self.text_color or "#000000"
        style.configure(".", background=bg, foreground=fg, borderwidth=self.border_width)
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg)
        button = self.button_colors
        if button is not None:
            btn_fg, btn_bg = button
            style.configure(
                "TButton",
                background=btn_bg or bg,
                foreground=btn_fg or fg,
            )
            active_bg = self._lighten(btn_bg or bg)
            style.map(
                "TButton",
                background=[("active", active_bg), ("pressed", active_bg)],
                foreground=[("active", btn_fg or fg)],
            )
        input_bg = self.input_background_color or bg
        input_fg = self.input_text_color or fg
        style.configure("TEntry", fieldbackground=input_bg, foreground=input_fg)
        style.configure("TSpinbox", fieldbackground=input_bg, foreground=input_fg)
        style.configure("TCombobox", fieldbackground=input_bg, foreground=input_fg)
        style.configure(
            "Treeview",
            background=input_bg or bg,
            fieldbackground=input_bg or bg,
            foreground=input_fg,
        )
        style.configure("Treeview.Heading", background=bg, foreground=fg)
        if self.slider_color is not None:
            style.configure("Horizontal.TScale", troughcolor=self.slider_color)
            style.configure("Vertical.TScale", troughcolor=self.slider_color)
        style.configure("TNotebook", background=bg, foreground=fg)
        style.configure("TNotebook.Tab", background=bg, foreground=fg)
        style.map("TNotebook.Tab", background=[("selected", input_bg or bg)])
        progress = self.progress_bar_colors
        if progress is not None:
            style.configure(
                "Horizontal.TProgressbar",
                background=progress[0] or bg,
                troughcolor=progress[1] or bg,
            )
            style.configure(
                "Vertical.TProgressbar",
                background=progress[0] or bg,
                troughcolor=progress[1] or bg,
            )

    @staticmethod
    def _lighten(color):
        """Lighten a #rrggbb color a bit for hover states (fallback: unchanged)."""
        try:
            value = color.lstrip("#")
            if len(value) != 6:
                return color
            parts = [int(value[i:i + 2], 16) for i in (0, 2, 4)]
            parts = [min(255, channel + 32) for channel in parts]
            return f"#{parts[0]:02x}{parts[1]:02x}{parts[2]:02x}"
        except Exception:
            return color


theme_manager = ThemeManager()


_UNSET = object()


def theme(name=_UNSET):
    """Get or set the current theme.

    ``theme()`` returns the current theme name (``None`` = system native).
    ``theme("DarkBlue3")`` applies a theme and returns its canonical name.
    ``theme(None)`` explicitly resets to the native system look and returns None.
    """
    if name is _UNSET:
        return theme_manager.name
    return theme_manager.apply(name)


def list_of_look_and_feel_values():
    """Sorted list of available theme names."""
    return sorted(LOOK_AND_FEEL_TABLE)


def theme_background_color(color=None):
    """Get or set the current theme's window background color."""
    if color is not None:
        theme_manager._entry()["BACKGROUND"] = color  # noqa: SLF001
    return theme_manager.background_color


def theme_text_color(color=None):
    """Get or set the current theme's text color."""
    if color is not None:
        theme_manager._entry()["TEXT"] = color  # noqa: SLF001
    return theme_manager.text_color


def theme_button_color(color=None):
    """Get or set the current theme's button (text, background) colors."""
    if color is not None:
        theme_manager._entry()["BUTTON"] = color  # noqa: SLF001
    return theme_manager.button_colors


def theme_input_background_color(color=None):
    """Get or set the current theme's input background color."""
    if color is not None:
        theme_manager._entry()["INPUT"] = color  # noqa: SLF001
    return theme_manager.input_background_color


def theme_input_text_color(color=None):
    """Get or set the current theme's input text color."""
    if color is not None:
        theme_manager._entry()["TEXT_INPUT"] = color  # noqa: SLF001
    return theme_manager.input_text_color


def theme_progress_bar_color(bar_color=None, background_color=None):
    """Get or set the current theme's progress bar (bar, trough) colors."""
    if bar_color is not None or background_color is not None:
        current = theme_manager.progress_bar_colors or (None, None)
        new_bar = bar_color if bar_color is not None else current[0]
        new_bg = background_color if background_color is not None else current[1]
        theme_manager._entry()["PROGRESS"] = (new_bar, new_bg)  # noqa: SLF001
    return theme_manager.progress_bar_colors


def theme_slider_color(color=None):
    """Get or set the current theme's slider color."""
    if color is not None:
        theme_manager._entry()["SCROLL"] = color  # noqa: SLF001
    return theme_manager.slider_color


def theme_border_width(width=None):
    """Get or set the current theme's border width."""
    if width is not None:
        theme_manager._entry()["BORDER"] = width  # noqa: SLF001
    return theme_manager.border_width


def theme_add_new(name, colors):
    """Register a new theme; returns the canonical name."""
    return theme_manager.add_new(name, colors)


def theme_global():
    """Baseline compatibility: returns the name to apply at startup (native)."""
    return None


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
        root = tk.Tk()
        root.withdraw()
    try:
        return sorted(ttk.Style(root).theme_names())
    finally:
        if temporary:
            root.destroy()


def ttk_theme(name=None):
    """Get or set the ttk engine theme on every open window.

    Independent from the 160 PySimpleGUI color themes: this selects the
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
