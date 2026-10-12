#!/usr/bin/env python3
"""TkSimpleGUI immutable constants.

Everything here is immutable (str/int/tuple/Enum). Mutable state lives in
the Settings and ThemeManager singletons, never at module level.
"""

from enum import Enum


class ButtonType(Enum):
    """Internal classification of button behaviours."""

    READ = "read"  # posts its key once on click
    REALTIME = "realtime"  # posts on press and release
    BROWSE_FILE = "browse_file"
    BROWSE_FILES = "browse_files"
    BROWSE_FOLDER = "browse_folder"
    SAVEAS_FILE = "saveas_file"
    CALENDAR_CHOOSER = "calendar_chooser"
    COLOR_CHOOSER = "color_chooser"
    CLOSES_WIN_ONLY = "closes_win_only"


class Location(Enum):
    """Vertical/horizontal placement hints (tabs, titles)."""

    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


# --- sentinel values -------------------------------------------------------
WIN_CLOSED = WINDOW_CLOSED = None
TIMEOUT_KEY = EVENT_TIMEOUT = "__TIMEOUT__"
TIMER_KEY = EVENT_TIMER = "__TIMER EVENT__"
THIS_ROW = 555666777
WRITE_ONLY_KEY = "__WRITE ONLY__"

# --- default look ----------------------------------------------------------
DEFAULT_ELEMENT_SIZE = (45, 1)
DEFAULT_BUTTON_ELEMENT_SIZE = (10, 1)
DEFAULT_MARGINS = (10, 5)
DEFAULT_ELEMENT_PADDING = (5, 3)
DEFAULT_FONT = ("Helvetica", 10)
DEFAULT_AUTOCLOSE_TIME = 3  # seconds
DEFAULT_TOOLTIP_TIME = 400  # milliseconds
DEFAULT_TOOLTIP_OFFSET = (0, -20)
DEFAULT_PROGRESS_BAR_SIZE = (20, 20)
DEFAULT_TABLE_NUM_ROWS = 10
DEFAULT_LISTBOX_SIZE = (20, 6)
# every window keeps the title-bar buttons (minimize/maximize/close)
# visible and clickable even when the user shrinks it hard
WINDOW_MIN_WIDTH = 140
WINDOW_MIN_HEIGHT = 60

COLOR_SYSTEM_DEFAULT = "1234567890"

RELIEF_RAISED = "raised"
RELIEF_SUNKEN = "sunken"
RELIEF_FLAT = "flat"
RELIEF_RIDGE = "ridge"
RELIEF_GROOVE = "groove"
RELIEF_SOLID = "solid"

MENU_DISABLED_CHARACTER = "!"
MENU_SHORTCUT_CHARACTER = "&"
MENU_KEY_SEPARATOR = "::"
MENU_SEPARATOR_LINE = "---"

# tk relief constants re-exported so user code does not need tkinter
FLAT = "flat"
GROOVE = "groove"
RAISED = "raised"
SUNKEN = "sunken"
RIDGE = "ridge"
SOLID = "solid"

BROWSE_FILES_DELIMITER = ";"
FILE_TYPES_ALL_FILES = (("ALL Files", "*.*"),)

DEFAULT_THREAD_KEY = "-THREAD DONE-"

# base64 icons: TkSimpleGUI badge (blue gradient rounded square, "Tk"/"T" mark);
# replaces the stock Tk feather icon. Not used by default (windows keep the
# interpreter's own icon unless icon= is passed).
DEFAULT_BASE64_ICON = (
    b"iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAADGElEQVR42uWb+2uOYRjHrz/BzzNzmG3MjJkxs4MdzIQccgg55JBDjFmzNWvGDHNKEkkSSRJJEkkiSSJJIknyl3z17od3757ua67neu7nvbf3vuvzy9t9fb7Xff3w1NP73ESK1XjuL0YiFMdaeOYPRjORDt/Q/xuZQOiD15/+hUxEdviTP5HJDHv4ur4f8AF2ALUnvsMHzIfv/QafGHL4Bce+wkeSA6jp+QIfGRzA0c/wkeQAqrs/wUeSA6jq+ggfGTh85ZEP8Bmq7HyPVNKxgplcrmmfFKmP5ne8QyrpWGPymyDJNe2TIvVRRftbpJKuAUhyTfukSH1UcfgNUknbAAS5pn1SpD6a1/YaqaRrAJJc0z4pUh+Vt75CkMTG/8EFSAlmcj5Tf5Ja7hzBWio/9BIa2IYd+KLU0tyWF9DAhbrwRamlOQefQwMX6sIXpZbKmp9BAxfqwhellsr2P4UGNjRmn2klfjc98CS5NHvfE2jgGo7bZzuXSvc+hgaukbh9tnOpdM8jaGAbidlnO5dm7X4IDVwjcfts51LJrgfQwDVi02daib2mB542l0p23ocGdgAWfbYzTNDMHfeggWvOps92hgmasf0uNHDN2fTZzjBBxdvuQAPXnE2f7QwTVLz1NjSwzVn2SV7DtZkJaPqWW9DANRy3z3YuFW2+CQ1cI3H7bOdS0aYb0MA2ErPPdi5N23gdGrhG4vbZzqXCDdeggWskHT7Jg1GaS4Xrr0ID27ADX5RamrruCjRwoS58UWppytrL0MCFuvBFqaWCNZeggQt14YtSSwWrL0IDG+rAJ12mWspfdQEauIZd+MK8RwRrKW/leWjgAlz4wgwgWEt5K85CAxvgwBdqAIFamry8Hxq4ABe+MAMI1lLuslPQYnpddeWT/isdrKPcpX3wmYEvxSYt6YWPJL8TnLj4OHwkOYAJTT3wkcEBLOqGjyQHML6xCz4y5M5ATkMnfMJ4aySnvgM+wN4ZGlfXDh8Y9uZYdm0bMhnR3cHsmlZkIqFvkI6tbkEmEOn+cFbVAYxmYrlRnlXZjJGI5iz/AD0vygRW7oWGAAAAAElFTkSuQmCC"
)
DEFAULT_BASE64_ICON_SMALL = (
    b"iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABZElEQVR42sWXsSuEcRjHv3+CGRFyESJEdC7X6bpSUlJSSkpKISJdXaEulyiDMhiUwWBQBoMyGAzKYFAGg8Ff8tXd8Oae7v1d7/fu3nvqM/4+z2f8PYBjkme/rAYIMlMnP6wlzuWJ42+GQcnl8ewXw6Ro+eTRJ+uBFxA7+KAflYzLm8cLmMi8049KpiGSostdWB5Nv9FFpQHl/Bjff2U58iKLXeRHOTfGdl+oYANUD0Z3nqlgA1QPRraeqGADVA+GNx6pYANUD4bWH6hgA1QPBtfuqWADVA8GVu+oYANUD/pXbqlgA1QP+pZvqGADVA96l66pYANUD3oWr6hgA1QPuhcuqWADVA+65i+oYANUDyJz51SwAaoHnbOnVLABqgcdMzkq2ADVU/gVtU9nGRQboDi8P2Fb6pAK/38+ynsvoDWZYT0oug1aEmmGScnrqDm+xzBw3odNsW3WkkCXcmN0k9XAteMPYerEZsUTu/0AAAAASUVORK5CYII="
)
DEFAULT_WINDOW_ICON = DEFAULT_BASE64_ICON
# 1x1 transparent PNG
BLANK_BASE64 = (
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)
