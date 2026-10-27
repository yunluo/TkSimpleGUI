#!/usr/bin/env python3
"""Typed enums replacing Tk's magic strings.

Every enum is a ``str`` subclass whose *value* is the literal string Tk
expects, so ``ts.Anchor.NW`` can be passed anywhere ``"nw"`` is accepted —
with IDE completion, typo protection (AttributeError instead of a silent
wrong layout) and discoverability.

    ts.TText("hi", anchor=ts.Anchor.CENTER)          # instead of "center"
    ts.TInput(justify=ts.Justify.RIGHT)              # instead of "right"
    ts.TFrame("T", layout, label_anchor=ts.Anchor.SE)
    element.bind(ts.EventType.DOUBLE_CLICK)         # instead of "<Double-1>"
"""

from enum import Enum


class _TkEnum(str, Enum):
    """Base for Tk string enums (values are the literal Tk strings)."""

    def __str__(self) -> str:  # str subclass: str() must give the Tk value
        return self.value


class Anchor(_TkEnum):
    """The 9-point anchor grid (tk ``anchor`` option / TFrame title)."""

    NW = "nw"
    N = "n"
    NE = "ne"
    W = "w"
    CENTER = "center"
    E = "e"
    SW = "sw"
    S = "s"
    SE = "se"


class LabelAnchor(_TkEnum):
    """ttk.Labelframe title positions (12-point grid)."""

    NW = "nw"
    N = "n"
    NE = "ne"
    EN = "en"
    E = "e"
    ES = "es"
    SE = "se"
    S = "s"
    SW = "sw"
    WN = "wn"
    W = "w"
    WS = "ws"


class Justify(_TkEnum):
    """Text alignment inside a widget."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class Relief(_TkEnum):
    """Border styles (tk ``relief`` option)."""

    RAISED = "raised"
    SUNKEN = "sunken"
    FLAT = "flat"
    RIDGE = "ridge"
    GROOVE = "groove"
    SOLID = "solid"


class Orientation(_TkEnum):
    """Widget orientation."""

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class Compound(_TkEnum):
    """How an image and text share space (ttk ``compound``)."""

    NONE = "none"
    TEXT = "text"
    IMAGE = "image"
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"


class State(_TkEnum):
    """Widget states."""

    NORMAL = "normal"
    DISABLED = "disabled"
    READONLY = "readonly"


class WrapMode(_TkEnum):
    """tk.Text line wrapping."""

    WORD = "word"
    CHAR = "char"
    NONE = "none"


class ProgressMode(_TkEnum):
    """ttk.Progressbar modes."""

    DETERMINATE = "determinate"
    INDETERMINATE = "indeterminate"


class SelectMode(_TkEnum):
    """Extended tk list selection modes (mirrors constants.SelectMode values)."""

    SINGLE = "single"
    BROWSE = "browse"
    MULTIPLE = "multiple"
    EXTENDED = "extended"


class Cursor(_TkEnum):
    """Common mouse cursors (tk accepts many more names)."""

    ARROW = "arrow"
    HAND1 = "hand1"
    HAND2 = "hand2"
    WATCH = "watch"
    XTERM = "xterm"
    CROSSHAIR = "crosshair"
    FLEUR = "fleur"
    SIZE_NW_SE = "size_nw_se"
    SIZING = "sizing"


class EventType(str, Enum):
    """Common tk event patterns as named constants.

    The value is the exact Tk binding pattern, so
    ``element.bind(ts.EventType.DOUBLE_CLICK)`` equals the string form.
    """

    CLICK = "<Button-1>"
    DOUBLE_CLICK = "<Double-1>"
    TRIPLE_CLICK = "<Triple-1>"
    RIGHT_CLICK = "<Button-3>"
    MIDDLE_CLICK = "<Button-2>"
    MOUSE_ENTER = "<Enter>"
    MOUSE_LEAVE = "<Leave>"
    MOUSE_MOTION = "<Motion>"
    FOCUS_IN = "<FocusIn>"
    FOCUS_OUT = "<FocusOut>"
    RETURN = "<Return>"
    ESCAPE = "<Escape>"
    ANY_KEY = "<Key>"
    KEY_RELEASE = "<KeyRelease>"
    SPACE = "<space>"
    DELETE = "<Delete>"
    RESIZE = "<Configure>"
    WHEEL = "<MouseWheel>"

    @staticmethod
    def control(letter: str) -> str:
        """``EventType.control("o")`` -> ``"<Control-o>"``."""
        return f"<Control-{letter}>"

    @staticmethod
    def shift(letter: str) -> str:
        """``EventType.shift("F5")`` -> ``"<Shift-F5>"``."""
        return f"<Shift-{letter}>"

    @staticmethod
    def alt(letter: str) -> str:
        """``EventType.alt("q")`` -> ``"<Alt-q>"``."""
        return f"<Alt-{letter}>"

    @staticmethod
    def key(name: str) -> str:
        """``EventType.key("F5")`` -> ``"<F5>"``; generic builder."""
        return f"<{name}>"


# Tk color names people actually use (the full X11 list is 700+; these are
# the common ones — any "#rrggbb" string still works everywhere).
class Color(str, Enum):
    """A curated set of Tk color names. ``str(Color.RED) == "red"``."""

    BLACK = "black"
    WHITE = "white"
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    YELLOW = "yellow"
    ORANGE = "orange"
    PURPLE = "purple"
    GRAY = "gray"
    GREY = "grey"
    LIGHT_GRAY = "lightgray"
    DARK_GRAY = "darkgray"
    CYAN = "cyan"
    MAGENTA = "magenta"
    BROWN = "brown"
    PINK = "pink"
    NAVY = "navy"
    TEAL = "teal"
    MAROON = "maroon"
    OLIVE = "olive"
    LIME = "lime"
    GOLD = "gold"
    SILVER = "silver"
    SYSTEM_BUTTON_FACE = "SystemButtonFace"
    SYSTEM_WINDOW = "SystemWindow"
    SYSTEM_HIGHLIGHT = "SystemHighlight"
