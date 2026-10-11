#!/usr/bin/env python3
"""PySimpleGUI4 - Python GUI Framework (object oriented, Python 3.4+).

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
    validate_integer,
    validate_float,
    validate_regex,
)

# --- window --------------------------------------------------------------------------
from .window import Window, SystemTray

# --- event manager ---------------------------------------------------------------------
from .event import PySimpleEvent, singleton_window

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
    "set_options", "get_options",
    "theme", "theme_manager", "list_of_look_and_feel_values",
    "theme_background_color", "theme_text_color", "theme_button_color",
    "theme_input_background_color", "theme_input_text_color",
    "theme_progress_bar_color", "theme_slider_color", "theme_border_width",
    "theme_add_new", "LOOK_AND_FEEL_TABLE",
    "Element", "InputElement", "ContainerElement",
    "Text", "Input", "InputText", "Combo", "OptionMenu", "Listbox", "Spin",
    "Checkbox", "CheckList", "Radio", "Slider", "Multiline", "Output",
    "ProgressBar", "Button", "Submit", "CloseButton", "Image", "Canvas",
    "Graph", "Shape", "Frame", "Column", "Splitter", "ScrollableColumn",
    "Toolbar", "LabeledEdit", "KeyValueEditor", "FlowPanel", "Calendar",
    "Tab", "TabGroup", "Menu", "Table", "Tree",
    "StatusBar", "VerticalSeparator", "HorizontalSeparator", "Sizegrip",
    "validate_integer", "validate_float", "validate_regex",
    "Window", "SystemTray", "PySimpleEvent", "singleton_window",
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
]


def main():
    """Print the version (placeholder for a future CLI)."""
    print("PySimpleGUI4", __version__)


if __name__ == "__main__":
    main()
