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

# base64 icons
DEFAULT_BASE64_ICON = (
    b"R0lGODlhIQAgAPcAAAAAADBpmDBqmTFqmjJrmzJsnDNtnTRrmTZtmzZumzRtnTdunDRunTRunjVv"
    b"nzdwnzhwnjlxnzVwoDZxoTdyojhzozl0ozh0pDp1pjp2pjp2pzx0oj12pD52pTt3qD54pjt4qDx4"
    b"qDx5qTx5qj16qj57qz57rD58rT98rkB4pkJ7q0J9rEB9rkF+rkB+r0d9qkZ/rEl7o0h8p0x9pk5/"
    b"p0l+qUB+sEyBrE2Crk2Er0KAsUKAskSCtEeEtUWEtkaGuEiHuEiHukiIu0qKu0mJvEmKvEqLvk2N"
    b"v1GErVGFr1SFrVGHslaHsFCItFSIs1COvlaPvFiJsVyRuWCNsWSPsWeQs2SQtGaRtW+Wt2qVuGmZ"
    b"v3GYuHSdv3ievXyfvV2XxGWZwmScx2mfyXafwHikyP7TPP/UO//UPP/UPf/UPv7UP//VQP/WQP/W"
    b"Qf/WQv/XQ//WRP7XSf/XSv/YRf/YRv/YR//YSP/YSf/YSv/ZS//aSv/aS/7YTv/aTP/aTf/bTv/b"
    b"T//cT/7aUf/cUP/cUf/cUv/cU//dVP/dVf7dVv/eVv/eV//eWP/eWf/fWv/fW/7cX/7cYf7cZP7e"
    b"Zf7dav7eb//gW//gXP/gXf/gXv/gX//gYP/hYf/hYv/iYf/iYv7iZP7iZf/iZv/kZv7iaP/kaP/k"
    b"a//ma//lbP/lbv/mbP/mbv7hdP7lcP/ncP/nc//ndv7gef7gev7iff7ke/7kfv7lf//ocf/ocv/o"
    b"dP/odv/peP/pe//ofIClw4Ory4GszoSszIqqxI+vyoSv0JGvx5OxyZSxyZSzzJi0y5m2zpC10pi7"
    b"15++16C6z6a/05/A2qHC3aXB2K3I3bLH2brP4P7jgv7jh/7mgf7lhP7mhf7liv/qgP7qh/7qiP7r"
    b"jf7sjP7nkv7nlv7nmP7pkP7qkP7rkv7rlv7slP7sl/7qmv7rnv7snv7sn/7un/7sqv7vq/7vrf7wp"
    b"v7wqf7wrv7wsv7wtv7ytv7zvP7zv8LU48LV5c3a5f70wP7z0AAAACH5BAEAAP8ALAAAAAAhACAAA"
    b"Aj/AP8JHEiwoMGDCA1uoYIF4bhK1vwlPOjlQICLApwVpFTGzBk1siYSrCLgoskFyQZKMsOypRyR/"
    b"GKYnBkgQbF/s8603KnmWkIaNIMaw6lzZ8tYB2cIWMo0KIJj/7YV9XgGDRo14gpOIUBggNevXpkKG"
    b"CDsXySradSoZcMmDsFnDxpEKEC3bl2uXCFQ+7emjV83bt7AgTNroJINAq0wWBxBgYHHdgt0+cdn"
    b"MJw5c+jQqYNnoARkAx04kPEvS4PTqBswuPIPUp06duzcsYMHT55wAjkwEahsQgqBNSQIHy582D9B"
    b"ePTs2dOnjx8/f1gJ9GXhRpTqApFQoDChu3cOAps///9D/g+gQvYGjrlw4cU/fUnYX6hAn34HgZMA"
    b"BQo0iJB/Qoe8UxAXOQiEg3wIXvCBQLUU4mAhh0R4SCLqJOSEBhhqkAEGHIYgUDaGICIiIoossogj"
    b"6yBUTQ4htNgiCCB4oIJAtJTIyI2MOOLIIxMtQQIJIwQZpAgwCKRNI43o6Igll1ySSTsI7dOECSaU"
    b"YOWVKwhkiyVMYuJlJpp0IpA6oJRTkBQopHnCmmu2IBA2mmQi5yZ0fgJKPP+2IwoooZwzkDQ2uCCo"
    b"CywUyoIW/5DDyaKefOPpJ6KU8w87pJgDTzqmDNSMDpzqYMOnn/7yTyiglBqKKKOMUopA7JgCy0Dd"
    b"eMEjUDM71GqrrcH8QwqqqpbiayqToqJKLwN5g45A0/TAw7LL2lrGP634aoopp5yiiiqrZLuKK+jg"
    b"444uBIHhw7g+MMsDFP/k4wq22rririu4xItLLriAUxAQ5ObrwzL/0PPKu7fIK3C8uxz0w8EIIwzM"
    b"P/cM7Dc98hxEzBBCBGGxxT8AwQzDujws7zcJQVMEEUKUbPITAt1D78OSivSFEUXEXATKA+HTscC8"
    b"AAA7"
)
DEFAULT_WINDOW_ICON = DEFAULT_BASE64_ICON
BLANK_BASE64 = b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
