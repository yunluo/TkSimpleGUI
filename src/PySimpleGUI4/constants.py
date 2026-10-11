#!/usr/bin/env python3
"""PySimpleGUI4 immutable constants.

Everything here is immutable (str/int/tuple/Enum). Mutable state lives in
the Settings and ThemeManager singletons, never at module level.
"""

from enum import Enum


class SelectMode(Enum):
    """Selection modes shared by Listbox and Table."""

    SINGLE = "single"
    BROWSE = "browse"
    MULTIPLE = "multiple"
    EXTENDED = "extended"


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

# base64 icons: PySimpleGUI4 badge (blue gradient rounded square, "P4"/"P" mark).
# Regenerate with _split/gen_logo.py; replaces the stock Tk feather icon.
DEFAULT_BASE64_ICON = (
    b"iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAADL0lEQVR42uXb+2vPURgH8OdP8PPMXGYbM2NmzOxiFzMhl1xiueSSS4xZszVrxgxzSxJJEkkSSRJJIkkiSSJJ8pe8tf3w3bOnc9b5fp/P5/P97HtOvX5Zz3ne5zw/rO937RClsBrP/0McURhr8dm/GMtUl28Y+INMkPTF68/8RiZyu/ypX8hko16+rv8nfGAdQO3JH/CB+fJ93+GTEZdfdPwbfJQYQE3vV/hoeADHvsBHiQFU93yGjxIDqOr+BB8NXb7y6Ef4jCq7PoALesn+YdDk0sLO9+CCXuPymyAzgqbJpYqOd+DCGIDMCJomlyqOvAUXygBERtA0ubSg/Q24MAYgM4KmyaXyttfgbM1SZVoyMxnJDN6lH5UffgXO2kzUuYqinyaD5re+BGdrJutcRdFPk0HzDr0AZ2sm61xF0U+TQWUtz8HZmsk6V1H002RQ2YFn4KzNRJ0rTT/TGvy5yy9a1wyau/8pOFszWedK0891ryaDSvc9AWdrJutcafq57tVkUOnex+CszUSdK00/172aDJqz5xE4WzNZ50rTz3WvJoNKdj8EF/Qa7Gn6hOiSq9lrqjOhkl0PwIXxXUBmmKRrL83eeR9cGAOQGSbp2kuzdtwDF8YAZIZJuvZS8fa74MIYgMwwSddeKt52B1zQX4eHDiIyTKJYplyaufU2ONsAZF3Qolime1DRllvgbBtlXdCiGoDMpaLNN8FZN4q6oEU2AJFLM5pvgLNtlHVBi2oAMpcKN10HZ9so68IQ5N8dbbUykwo3XgNnHYCoixPNmWn6hqvgbM1kXZxozkzT1l8BZ2sm6+JEc2YqWHcZnK2ZrIsTzZmpYO0lcNZmoi5ONGem/DUXwdmaybo40ZyZ8lZfAGdrJuviRHNmylt1Dpy1maiLE82ZaerKAXC2ZrIuTjRnptwVpyGZPkGZ6uIk1TNT7vJ++GzoP8WmLOuDjxL/Jzh56Qn4KDGASU298NHwAJb0wEeJAUxs7IaPRrwZyGnogk+Mr0Zy6jvhA+uboQl1HfDBqC/Hsmvbkcmc3g5m17QhEyX9gnR8dSsyger9cFbVQYxlobwoz6psQRylcpf/FmRIZFUKzhMAAAAASUVORK5CYII="
)
DEFAULT_BASE64_ICON_SMALL = (
    b"iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABfUlEQVR42sXXwStEURQG8PMnWCNCJkKEiMZkGk1TSkpKSklJKUSkqSnURKIslIWFsrCwUBYWysLCQllYKAsLC3/JpzeL153TvHM60503p367b879NnN7l0iY7PkffCDLTJ3+opbEwzPHP4hDxcPTxW/EqezwyaMv1ENYIHXwiSjWkXZxYYGJwgeiWKchkYO0z1U6PJl/h6SaAtpOF43vv0HCl2vc0XYHaGz3FRJewHeeRndeIOELfedpZOsZEr7Qd56GN54g4Qt952lo/RESvtB3ngbXHiCxTvAb91+h7aeB1XtIqrkHtJ0u6l+5g6SaAtpOF/Ut30JivYgC2k4X9S7dQMILaHkr6lm8hoQX0PJW1L1wBQkvoOWtqGv+EhJeQMtbUWLuAhJeQMtbUefsGSS8gJa3oo6ZE0h4AS1vVfoqap8uIgovIGWtwm/CttwhJO4lo2UtwgKt2QLqoext0JLJI04VX0fN6T3EQXwfNqW2UUuml3JjchM+SGf8A7A++g4MFES7AAAAAElFTkSuQmCC"
)
DEFAULT_WINDOW_ICON = DEFAULT_BASE64_ICON
BLANK_BASE64 = b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
