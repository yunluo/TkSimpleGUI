# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""TkSimpleGUI - Python GUI Framework (object oriented, Python 3.7+).

Usage::

    import TkSimpleGUI as sg

    layout = [
        [ts.TText("Hello")],
        [ts.TInput(key="-IN-"), ts.TButton("OK")],
    ]
    window = ts.Window("Demo", layout)
    event, values = window.read()
    window.close()
"""

from ._version import __version__, __author__, __email__, __license__

from . import constants as C  # noqa: F401

# --- typed enums (kill the magic strings) -----------------------------------------------
# ts.Anchor.CENTER instead of "center", ts.EventType.DOUBLE_CLICK instead of
# "<Double-1>" ... every enum's value IS the Tk string, so mixing styles works.
from .enums import (
    Anchor,
    LabelAnchor,
    Justify,
    Relief,
    Orientation,
    Compound,
    State,
    WrapMode,
    ProgressMode,
    SelectMode,
    Cursor,
    EventType,
    Color,
)

# --- constants ---------------------------------------------------------------
from .constants import (
    WIN_CLOSED,
    TIMEOUT_KEY,
    TIMER_KEY,
    ButtonType,
    Location,
    DEFAULT_ELEMENT_SIZE,
    DEFAULT_BUTTON_ELEMENT_SIZE,
    DEFAULT_MARGINS,
    DEFAULT_ELEMENT_PADDING,
    DEFAULT_FONT,
    DEFAULT_AUTOCLOSE_TIME,
    DEFAULT_PROGRESS_BAR_SIZE,
    COLOR_SYSTEM_DEFAULT,
    BROWSE_FILES_DELIMITER,
    FILE_TYPES_ALL_FILES,
    DEFAULT_BASE64_ICON,
    DEFAULT_BASE64_ICON_SMALL,
    BLANK_BASE64,
)

# --- utils --------------------------------------------------------------------
from .utils import (
    rgb,
    Timer,
    timer_start,
    timer_stop,
    formatted_datetime_now,
    running_windows,
    running_linux,
    running_mac,
    set_dpi_awareness,
    font_families,
    font_measure,
    font_actual,
)

# --- settings -------------------------------------------------------------------
from .settings import settings

# --- theme -----------------------------------------------------------------------
from ._theming import (
    theme,
    theme_manager,
    theme_list,
    theme_background_color,
    theme_text_color,
    theme_button_color,
    theme_input_background_color,
    theme_input_text_color,
    theme_progress_bar_color,
    theme_slider_color,
    theme_border_width,
    theme_add,
    ttk_theme,
    ttk_themes,
    THEMES,
)

# --- elements ----------------------------------------------------------------------
from .elements import (
    Element,
    InputElement,
    ContainerElement,
    TText,
    TInput,
    TCombo,
    TOptionMenu,
    TListbox,
    TSpin,
    TCheckbox,
    TCheckList,
    TRadio,
    TSlider,
    TMultiline,
    TOutput,
    TProgressBar,
    TButton,
    TSubmit,
    TCloseButton,
    TImage,
    TCanvas,
    TGraph,
    TShape,
    TFrame,
    TColumn,
    TSplitter,
    TScrollableColumn,
    TToolbar,
    TLabeledEdit,
    TKeyValueEditor,
    TFlowPanel,
    TCalendar,
    TTab,
    TTabGroup,
    TMenu,
    TTable,
    TTree,
    TStatusBar,
    TVerticalSeparator,
    THorizontalSeparator,
    TSizegrip,
    TMenubutton,
    TScrollbar,
    TRoundButton,
    TImageButton,
    TTextProgressBar,
    TGauge,
    TLED,
    TChart,
    ChartType,
    TTag,
    TBadge,
    TAvatar,
    TStatistic,
    TEmpty,
    TResult,
    TSkeleton,
    TAlert,
    TWatermark,
    TCard,
    TDescriptions,
    TSteps,
    TTimeline,
    TSegmented,
    TRate,
    TPagination,
    TTransfer,
    validate_integer,
    validate_float,
    validate_regex,
)

# --- window --------------------------------------------------------------------------
from .window import Window, SystemTray

# --- event manager ---------------------------------------------------------------------
from .event import (
    TkSimpleEvent,
    singleton_window,
    default_app,
    run_application,
)


def bind_event(event_names):
    """Register an ``on_*`` handler on the global default event manager.

    The recommended way to wire events — no imports beyond ``sg``, no
    explicit manager::

        @ts.bind_event("OK")
        def on_ok(window, values):
            ts.popup(f"hi {values['-IN-']}")

        ts.Window("Demo", layout).run()   # handler fires inside .run()

    ``event_names`` is one key or a list of keys; the handler must be named
    with an ``on_`` prefix. The same manager also accepts ``bind_event``
    directly (``ts.default_app().bind_event``).
    """
    return default_app().bind_event(event_names)


def main_loop(window, app=None):
    """Run the single application event loop (user code never writes one).

    The lighter form is ``window.run()`` / ``ts.SystemTray(...).run()`` —
    same loop, called on the root object itself.
    """
    return run_application(window, app=app)

# --- actions ------------------------------------------------------------------------------
from .actions import Action, ActionList

# --- declarative config objects (dataclasses) ----------------------------------------------
from .config import ElementOptions, WindowConfig

# --- Windows desktop integration (no-op off Windows) ----------------------------------------
from .hotkey import GlobalHotkeys, taskbar_progress
from .input_blocker import block_input, unblock_input

# --- user settings / animation --------------------------------------------------------
from .user_settings import UserSettings
from .animation import fade_in, fade_out, slide, animate_progress

# --- logging into an TOutput / TMultiline element ----------------------------------------
from .logger import Logger, find_log_element, log

# --- popups ------------------------------------------------------------------------------
from .popup import (
    popup,
    popup_ok,
    popup_yes_no,
    popup_ok_cancel,
    popup_cancel,
    popup_error,
    popup_scrolled,
    popup_no_buttons,
    popup_auto_close,
    popup_notify,
    popup_get_text,
    popup_get_file,
    popup_get_folder,
    popup_get_date,
    popup_get_font,
    popup_find,
    popup_replace,
)


__all__ = [
    "__version__", "__author__", "__email__", "__license__",
    "WIN_CLOSED", "TIMEOUT_KEY", "TIMER_KEY",
    "SelectMode", "ButtonType", "Location",
    "DEFAULT_ELEMENT_SIZE", "DEFAULT_BUTTON_ELEMENT_SIZE", "DEFAULT_MARGINS",
    "DEFAULT_ELEMENT_PADDING", "DEFAULT_FONT", "DEFAULT_AUTOCLOSE_TIME",
    "DEFAULT_PROGRESS_BAR_SIZE", "COLOR_SYSTEM_DEFAULT",
    "BROWSE_FILES_DELIMITER", "FILE_TYPES_ALL_FILES",
    "DEFAULT_BASE64_ICON", "DEFAULT_BASE64_ICON_SMALL",
    "BLANK_BASE64",
    "rgb", "Timer", "timer_start", "timer_stop", "formatted_datetime_now",
    "running_windows", "running_linux", "running_mac", "set_dpi_awareness",
    "font_families", "font_measure", "font_actual",
    "settings",
    "theme", "theme_manager", "theme_list",
    "theme_background_color", "theme_text_color", "theme_button_color",
    "theme_input_background_color", "theme_input_text_color",
    "theme_progress_bar_color", "theme_slider_color", "theme_border_width",
    "theme_add", "THEMES",
    "ttk_theme", "ttk_themes",
    "Element", "InputElement", "ContainerElement",
    "TText", "TInput", "TCombo", "TOptionMenu", "TListbox", "TSpin",
    "TCheckbox", "TCheckList", "TRadio", "TSlider", "TMultiline", "TOutput",
    "TProgressBar", "TButton", "TSubmit", "TCloseButton", "TImage", "TCanvas",
    "TGraph", "TShape", "TFrame", "TColumn", "TSplitter", "TScrollableColumn",
    "TToolbar", "TLabeledEdit", "TKeyValueEditor", "TFlowPanel", "TCalendar",
    "TTab", "TTabGroup", "TMenu", "TTable", "TTree",
    "TStatusBar", "TVerticalSeparator", "THorizontalSeparator", "TSizegrip",
    "TMenubutton", "TScrollbar",
    "TRoundButton", "TImageButton", "TTextProgressBar", "TGauge", "TLED",
    "TChart", "ChartType",
    "TTag", "TBadge", "TAvatar", "TStatistic", "TEmpty", "TResult", "TSkeleton",
    "TAlert", "TWatermark", "TCard", "TDescriptions", "TSteps", "TTimeline",
    "TSegmented", "TRate", "TPagination", "TTransfer",
    "validate_integer", "validate_float", "validate_regex",
    "Window", "SystemTray", "TkSimpleEvent", "singleton_window", "main_loop",
    "default_app", "run_application", "bind_event",
    "Action", "ActionList", "UserSettings", "GlobalHotkeys", "taskbar_progress",
    "block_input", "unblock_input",
    "Logger", "find_log_element", "log",
    "ElementOptions", "WindowConfig",
    "fade_in", "fade_out", "slide", "animate_progress", "dbg",
    "popup", "popup_ok", "popup_yes_no", "popup_ok_cancel", "popup_cancel",
    "popup_error", "popup_scrolled", "popup_no_buttons", "popup_auto_close",
    "popup_notify", "popup_get_text",
    "popup_get_file", "popup_get_folder", "popup_get_date",
    "popup_get_font", "popup_find", "popup_replace",
    "Anchor", "LabelAnchor", "Justify", "Relief", "Orientation", "Compound",
    "State", "WrapMode", "ProgressMode", "SelectMode", "Cursor",
    "EventType", "Color",
]


def dbg(*args, **kwargs):
    """Print into a quick auto-closing debug popup (TkSimpleGUI dbg)."""
    text = " ".join(
        str(arg) if not isinstance(arg, str) else arg for arg in args
    )
    return popup_no_buttons(text, title=kwargs.get("title", "Debug"))


def main(argv=None):
    """Command line entry: ``python -m TkSimpleGUI [--version | --themes]``."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="TkSimpleGUI", description="TkSimpleGUI GUI framework"
    )
    parser.add_argument(
        "--version", action="store_true", help="print the version and exit"
    )
    parser.add_argument(
        "--themes", action="store_true", help="list the available themes and exit"
    )
    options = parser.parse_args(argv)
    if options.version:
        print("TkSimpleGUI", __version__)
    elif options.themes:
        for name in theme_list():
            print(name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
