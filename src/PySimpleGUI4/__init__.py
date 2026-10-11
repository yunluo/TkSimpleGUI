#!/usr/bin/env python3
"""PySimpleGUI4 - Python GUI Framework (object oriented, Python 3.7+).

Usage::

    import PySimpleGUI4 as sg

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
    validate_integer,
    validate_float,
    validate_regex,
)

# --- window --------------------------------------------------------------------------
from .window import Window, SystemTray

# --- event manager ---------------------------------------------------------------------
from .event import PySimpleEvent, singleton_window
from .window.window import Window as _WindowClass


def main_loop(window, app=None):
    """Run the single application event loop (user code never writes one).

    Every event from every window is dispatched through the global event
    manager (``@app.bind_event`` + ``on_*`` handlers) and window ``Action``
    callbacks. The loop ends when the last window closes::

        app = sg.PySimpleEvent()

        @app.bind_event("OK")
        def on_ok(window, values):
            sg.popup(f"hi {values['-IN-']}")

        window = sg.Window("Demo", layout)
        sg.main_loop(window, app)          # that's the whole program
    """
    if app is None:
        app = PySimpleEvent()
    return app.run_event(window)

# --- actions ------------------------------------------------------------------------------
from .actions import Action, ActionList

# --- Windows desktop integration (no-op off Windows) ----------------------------------------
from .hotkey import GlobalHotkeys, taskbar_progress

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

# --- convenience aliases (PySimpleGUI style) ---------------------------------------------
I = Input
T = Text
B = Button
Btn = Button
DD = Combo
Drop = Combo
Dropdown = Combo
LB = Listbox
CB = Checkbox
Check = Checkbox
Rad = Radio
Sp = Spin
ML = Multiline
ProgBar = ProgressBar
Progress = ProgressBar
Col = Column
SBar = StatusBar
VS = VerticalSeparator
HS = HorizontalSeparator
FlexForm = Window
RGB = rgb
SetOptions = set_options
PopUp = popup

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
    "RoundButton", "ImageButton", "TextProgressBar",
    "validate_integer", "validate_float", "validate_regex",
    "Window", "SystemTray", "PySimpleEvent", "singleton_window", "main_loop",
    "Action", "ActionList", "UserSettings", "GlobalHotkeys", "taskbar_progress",
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
    "I", "T", "B", "Btn", "DD", "Drop", "Dropdown", "LB", "CB", "Check",
    "Rad", "Sp", "ML", "ProgBar", "Progress", "Col", "SBar", "VS", "HS",
    "FlexForm", "RGB", "SetOptions", "PopUp",
    "TText", "TInput", "TInputText", "TCombo", "TOptionMenu", "TListbox",
    "TSpin", "TCheckbox", "TCheckList", "TRadio", "TSlider", "TMultiline",
    "TOutput", "TProgressBar", "TButton", "TSubmit", "TCloseButton",
    "TImage", "TCanvas", "TGraph", "TShape", "TFrame", "TColumn",
    "TSplitter", "TScrollableColumn", "TToolbar", "TLabeledEdit",
    "TKeyValueEditor", "TFlowPanel", "TCalendar", "TTab", "TTabGroup",
    "TMenu", "TTable", "TTree", "TStatusBar", "TVerticalSeparator",
    "THorizontalSeparator", "TSizegrip", "TMenubutton", "TScrollbar",
    "TRoundButton", "TImageButton", "TTextProgressBar",
]


def dbg(*args, **kwargs):
    """Print into a quick auto-closing debug popup (PySimpleGUI dbg)."""
    text = " ".join(
        str(arg) if not isinstance(arg, str) else arg for arg in args
    )
    return popup_quick(text, title=kwargs.get("title", "Debug"))


def main(argv=None):
    """Command line entry: ``python -m PySimpleGUI4 [--version | --themes]``."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="PySimpleGUI4", description="PySimpleGUI4 GUI framework"
    )
    parser.add_argument(
        "--version", action="store_true", help="print the version and exit"
    )
    parser.add_argument(
        "--themes", action="store_true", help="list the available themes and exit"
    )
    options = parser.parse_args(argv)
    if options.version:
        print("PySimpleGUI4", __version__)
    elif options.themes:
        for name in list_of_look_and_feel_values():
            print(name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
