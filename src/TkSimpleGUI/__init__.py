# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""TkSimpleGUI - Python GUI Framework (object oriented, Python 3.7+).

Usage::

    import TkSimpleGUI as sg

    layout = [
        [sg.Text("Hello")],
        [sg.Input(key="-IN-"), sg.Button("OK")],
    ]
    window = sg.Window("Demo", layout)
    event, values = window.read()
    window.close()
"""

from ._version import __version__, version, __author__, __email__, __license__, port

from . import constants as C  # noqa: F401

# --- typed enums (kill the magic strings) -----------------------------------------------
# sg.Anchor.CENTER instead of "center", sg.EventType.DOUBLE_CLICK instead of
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
    SelectMode as EnumSelectMode,
    Cursor,
    EventType,
    Color,
)

# --- constants ---------------------------------------------------------------
from .constants import (
    WIN_CLOSED,
    WINDOW_CLOSED,
    TIMEOUT_KEY,
    EVENT_TIMEOUT,
    TIMER_KEY,
    EVENT_TIMER,
    THIS_ROW,
    WRITE_ONLY_KEY,
    SelectMode,
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
    RELIEF_RAISED,
    RELIEF_SUNKEN,
    RELIEF_FLAT,
    RELIEF_RIDGE,
    RELIEF_GROOVE,
    RELIEF_SOLID,
    BROWSE_FILES_DELIMITER,
    FILE_TYPES_ALL_FILES,
    DEFAULT_BASE64_ICON,
    DEFAULT_BASE64_ICON_SMALL,
    DEFAULT_WINDOW_ICON,
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
    running_trinket,
    running_replit,
    set_dpi_awareness,
    font_families,
    font_measure,
    font_actual,
)

# --- settings -------------------------------------------------------------------
from .settings import set_options, get_options

# --- theme -----------------------------------------------------------------------
from ._theming import (
    theme,
    theme_manager,
    list_of_look_and_feel_values,
    theme_background_color,
    theme_text_color,
    theme_button_color,
    theme_input_background_color,
    theme_input_text_color,
    theme_progress_bar_color,
    theme_slider_color,
    theme_border_width,
    theme_add_new,
    ttk_theme,
    ttk_themes,
    LOOK_AND_FEEL_TABLE,
)

# --- elements ----------------------------------------------------------------------
from .elements import (
    Element,
    InputElement,
    ContainerElement,
    Text,
    Input,
    InputText,
    Combo,
    OptionMenu,
    Listbox,
    Spin,
    Checkbox,
    CheckList,
    Radio,
    Slider,
    Multiline,
    Output,
    ProgressBar,
    Button,
    Submit,
    CloseButton,
    Image,
    Canvas,
    Graph,
    Shape,
    Frame,
    Column,
    Splitter,
    ScrollableColumn,
    Toolbar,
    LabeledEdit,
    KeyValueEditor,
    FlowPanel,
    Calendar,
    Tab,
    TabGroup,
    Menu,
    Table,
    Tree,
    StatusBar,
    VerticalSeparator,
    HorizontalSeparator,
    Sizegrip,
    Menubutton,
    Scrollbar,
    RoundButton,
    ImageButton,
    TextProgressBar,
    LED,
    Chart,
    ChartType,
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
from .window.window import Window as _WindowClass


def bind_event(event_names):
    """Register an ``on_*`` handler on the global default event manager.

    The recommended way to wire events — no imports beyond ``sg``, no
    explicit manager::

        @sg.bind_event("OK")
        def on_ok(window, values):
            sg.popup(f"hi {values['-IN-']}")

        sg.Window("Demo", layout).run()   # handler fires inside .run()

    ``event_names`` is one key or a list of keys; the handler must be named
    with an ``on_`` prefix. The same manager also accepts ``bind_event``
    directly (``sg.default_app().bind_event``).
    """
    return default_app().bind_event(event_names)


def on_event(event_names):
    """Alias of :func:`bind_event` (reads naturally as a decorator)."""
    return default_app().bind_event(event_names)


def main_loop(window, app=None):
    """Run the single application event loop (user code never writes one).

    The lighter form is ``window.run()`` / ``sg.SystemTray(...).run()`` —
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

# --- user settings / i18n / animation --------------------------------------------------------
from .user_settings import UserSettings
from .i18n import (
    _,
    translate,
    set_translations,
    add_translation,
    clear_translations,
)
from .animation import fade_in, fade_out, slide, animate_progress

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
    popup_non_blocking,
    popup_quick,
    popup_quick_message,
    popup_auto_close,
    popup_timed,
    popup_annoying,
    popup_no_titlebar,
    popup_notify,
    popup_get_text,
    popup_get_file,
    popup_get_folder,
    popup_get_date,
    popup_get_font,
    popup_find,
    popup_replace,
    popup_error_with_traceback,
    MsgBox,
)

# --- T-prefixed aliases (uniform prefix rule) --------------------------------------------
# Every widget is also importable by its own name with a "T" prefix
# (TText = Text, TButton = Button, TRoundButton = RoundButton, ...) —
# a single mechanical rule, no renames. Both spellings are the same class;
# existing sg.Text style code keeps working.
TText = Text
TInput = Input
TInputText = InputText
TCombo = Combo
TOptionMenu = OptionMenu
TListbox = Listbox
TSpin = Spin
TCheckbox = Checkbox
TCheckList = CheckList
TRadio = Radio
TSlider = Slider
TMultiline = Multiline
TOutput = Output
TProgressBar = ProgressBar
TButton = Button
TSubmit = Submit
TCloseButton = CloseButton
TImage = Image
TCanvas = Canvas
TGraph = Graph
TShape = Shape
TFrame = Frame
TColumn = Column
TSplitter = Splitter
TScrollableColumn = ScrollableColumn
TToolbar = Toolbar
TLabeledEdit = LabeledEdit
TKeyValueEditor = KeyValueEditor
TFlowPanel = FlowPanel
TCalendar = Calendar
TTab = Tab
TTabGroup = TabGroup
TMenu = Menu
TTable = Table
TTree = Tree
TStatusBar = StatusBar
TVerticalSeparator = VerticalSeparator
THorizontalSeparator = HorizontalSeparator
TSizegrip = Sizegrip
TMenubutton = Menubutton
TScrollbar = Scrollbar
TRoundButton = RoundButton
TImageButton = ImageButton
TTextProgressBar = TextProgressBar
TLED = LED
TChart = Chart

__all__ = [
    "__version__", "version", "__author__", "__email__", "__license__", "port",
    "WIN_CLOSED", "WINDOW_CLOSED", "TIMEOUT_KEY", "EVENT_TIMEOUT", "TIMER_KEY",
    "EVENT_TIMER", "THIS_ROW", "WRITE_ONLY_KEY",
    "SelectMode", "ButtonType", "Location",
    "DEFAULT_ELEMENT_SIZE", "DEFAULT_BUTTON_ELEMENT_SIZE", "DEFAULT_MARGINS",
    "DEFAULT_ELEMENT_PADDING", "DEFAULT_FONT", "DEFAULT_AUTOCLOSE_TIME",
    "DEFAULT_PROGRESS_BAR_SIZE", "COLOR_SYSTEM_DEFAULT",
    "RELIEF_RAISED", "RELIEF_SUNKEN", "RELIEF_FLAT", "RELIEF_RIDGE",
    "RELIEF_GROOVE", "RELIEF_SOLID",
    "BROWSE_FILES_DELIMITER", "FILE_TYPES_ALL_FILES",
    "DEFAULT_BASE64_ICON", "DEFAULT_BASE64_ICON_SMALL", "DEFAULT_WINDOW_ICON",
    "BLANK_BASE64",
    "rgb", "Timer", "timer_start", "timer_stop", "formatted_datetime_now",
    "running_windows", "running_linux", "running_mac", "running_trinket",
    "running_replit", "set_dpi_awareness",
    "font_families", "font_measure", "font_actual",
    "set_options", "get_options",
    "theme", "theme_manager", "list_of_look_and_feel_values",
    "theme_background_color", "theme_text_color", "theme_button_color",
    "theme_input_background_color", "theme_input_text_color",
    "theme_progress_bar_color", "theme_slider_color", "theme_border_width",
    "theme_add_new", "LOOK_AND_FEEL_TABLE",
    "ttk_theme", "ttk_themes",
    "Element", "InputElement", "ContainerElement",
    "Text", "Input", "InputText", "Combo", "OptionMenu", "Listbox", "Spin",
    "Checkbox", "CheckList", "Radio", "Slider", "Multiline", "Output",
    "ProgressBar", "Button", "Submit", "CloseButton", "Image", "Canvas",
    "Graph", "Shape", "Frame", "Column", "Splitter", "ScrollableColumn",
    "Toolbar", "LabeledEdit", "KeyValueEditor", "FlowPanel", "Calendar",
    "Tab", "TabGroup", "Menu", "Table", "Tree",
    "StatusBar", "VerticalSeparator", "HorizontalSeparator", "Sizegrip",
    "Menubutton", "Scrollbar",
    "RoundButton", "ImageButton", "TextProgressBar", "LED", "Chart", "ChartType",
    "validate_integer", "validate_float", "validate_regex",
    "Window", "SystemTray", "TkSimpleEvent", "singleton_window", "main_loop",
    "default_app", "run_application", "bind_event", "on_event",
    "Action", "ActionList", "UserSettings", "GlobalHotkeys", "taskbar_progress",
    "block_input", "unblock_input",
    "ElementOptions", "WindowConfig",
    "_", "translate", "set_translations", "add_translation",
    "clear_translations",
    "fade_in", "fade_out", "slide", "animate_progress", "dbg",
    "popup", "popup_ok", "popup_yes_no", "popup_ok_cancel", "popup_cancel",
    "popup_error", "popup_scrolled", "popup_no_buttons", "popup_non_blocking",
    "popup_quick", "popup_quick_message", "popup_auto_close", "popup_timed",
    "popup_annoying", "popup_no_titlebar", "popup_notify", "popup_get_text",
    "popup_get_file", "popup_get_folder", "popup_get_date",
    "popup_get_font", "popup_find", "popup_replace",
    "popup_error_with_traceback", "MsgBox",
    "TText", "TInput", "TInputText", "TCombo", "TOptionMenu", "TListbox",
    "TSpin", "TCheckbox", "TCheckList", "TRadio", "TSlider", "TMultiline",
    "TOutput", "TProgressBar", "TButton", "TSubmit", "TCloseButton",
    "TImage", "TCanvas", "TGraph", "TShape", "TFrame", "TColumn",
    "TSplitter", "TScrollableColumn", "TToolbar", "TLabeledEdit",
    "TKeyValueEditor", "TFlowPanel", "TCalendar", "TTab", "TTabGroup",
    "TMenu", "TTable", "TTree", "TStatusBar", "TVerticalSeparator",
    "THorizontalSeparator", "TSizegrip", "TMenubutton", "TScrollbar",
    "TRoundButton", "TImageButton", "TTextProgressBar", "TLED", "TChart",
    "Anchor", "LabelAnchor", "Justify", "Relief", "Orientation", "Compound",
    "State", "WrapMode", "ProgressMode", "EnumSelectMode", "Cursor",
    "EventType", "Color",
]


def dbg(*args, **kwargs):
    """Print into a quick auto-closing debug popup (TkSimpleGUI dbg)."""
    text = " ".join(
        str(arg) if not isinstance(arg, str) else arg for arg in args
    )
    return popup_quick(text, title=kwargs.get("title", "Debug"))


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
        for name in list_of_look_and_feel_values():
            print(name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
