#!/usr/bin/env python3
"""Panel and structure elements: Card, Descriptions, Steps and Timeline.

- :class:`Card` -- an outlined panel with an optional header (title,
  subtitle, trailing extra element) around a nested layout
- :class:`Descriptions` -- an aligned label/value list, optionally bordered
- :class:`Steps` -- a horizontal or vertical step indicator (canvas-drawn)
- :class:`Timeline` -- a vertical activity feed with dots and timestamps
  (canvas-drawn)

Card and Descriptions compose real tk widgets, so the controls nested in a
card keep their native behaviour. Steps and Timeline paint every figure on
a private canvas and re-derive their colors from the active theme on each
redraw -- a color passed in explicitly always wins over the theme.
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, List, Optional, Tuple

from . import _paint
from .base import ContainerElement, Element
from .. import _theming as theme_mod
from .. import settings as settings_mod

# Parsed item forms: Descriptions (label, value), Steps (title, description)
# and Timeline (timestamp, content, type, color).
DescriptionItem = Tuple[str, Any]
StepItem = Tuple[str, Optional[str]]
TimelineItem = Tuple[Any, str, Optional[str], Optional[str]]


def _as_text(value):
    """Text form of a display value ("" for None)."""
    return "" if value is None else str(value)


def _parse_descriptions(items):
    """Normalise ``items`` (a dict or (label, value) pairs) into tuples.

    Labels become strings (they are display text); values keep the object
    they were given, so ``get()`` hands back exactly what was passed in.
    """
    if isinstance(items, dict):
        pairs = list(items.items())
    else:
        pairs = []
        for entry in items:
            if isinstance(entry, (list, tuple)):
                label = entry[0] if len(entry) > 0 else ""
                value = entry[1] if len(entry) > 1 else None
            else:
                label = entry
                value = None
            pairs.append((label, value))
    return [(str(label), value) for label, value in pairs]


def _parse_steps(items):
    """Normalise step titles and ``(title, description)`` pairs to tuples."""
    steps: List[StepItem] = []
    for entry in items:
        if isinstance(entry, (list, tuple)):
            title = entry[0] if len(entry) > 0 else ""
            description = entry[1] if len(entry) > 1 else None
        else:
            title = entry
            description = None
        steps.append((str(title), None if description is None else str(description)))
    return steps


def _parse_timeline(items):
    """Normalise the three accepted timeline entry forms to 4-tuples.

    A plain string is content only, ``(timestamp, content)`` adds a time
    line, and a dict may also carry ``type`` (semantic dot color) and
    ``color`` (an explicit dot color that wins over the type). A mapping
    in the second slot of the pair — ``("10:02", {"content": ..., ...})``
    — supplies the fields, with the pair's first element as the fallback
    timestamp, so either spelling reads naturally.
    """
    entries: List[TimelineItem] = []
    for item in items:
        if isinstance(item, dict):
            stamp = item.get("timestamp")
            content = _as_text(item.get("content"))
            kind = item.get("type")
            color = item.get("color")
        elif isinstance(item, (list, tuple)):
            stamp = item[0] if len(item) > 0 else None
            extra = item[1] if len(item) > 1 else None
            if isinstance(extra, dict):
                stamp = extra.get("timestamp", stamp)
                content = _as_text(extra.get("content"))
                kind = extra.get("type")
                color = extra.get("color")
            else:
                content = _as_text(extra)
                kind = None
                color = None
        else:
            stamp = None
            content = _as_text(item)
            kind = None
            color = None
        entries.append((stamp, content, kind, color))
    return entries


def _has_timestamp(stamp):
    """True when a timeline entry carries a usable timestamp."""
    return stamp is not None and str(stamp) != ""


class Card(ContainerElement):
    """An outlined panel around a nested layout.

    Tk has no drop shadow, so the card is expressed with a 1px outline and
    layered background colors instead: an optional header (``title``,
    ``subtitle`` and the trailing ``extra`` element), a hairline separator
    and a body that owns ``layout``::

        ts.Card(
            "Server",
            [[ts.Text("Host"), ts.Input(key="-HOST-")]],
            subtitle="prod-01",
            extra=ts.Button("Restart", key="-RESTART-"),
        )

    ``extra`` is built into the header, so it must not appear in ``layout``
    as well.
    """

    __slots__ = (
        "_title",
        "_subtitle",
        "_extra",
        "_background_color",
        "_border_color",
        "_padding",
        "_font",
        "_header",
        "_header_text",
        "_title_label",
        "_subtitle_label",
        "_separator",
        "_body",
    )

    # created together in _create_widget
    _header: Optional[tk.Frame]
    _header_text: Optional[tk.Frame]
    _title_label: Optional[ttk.Label]
    _subtitle_label: Optional[ttk.Label]
    _separator: Optional[tk.Frame]
    _body: Optional[tk.Frame]

    def __init__(
        self,
        title=None,
        layout=(),
        subtitle=None,
        extra=None,
        size=(None, None),
        background_color=None,
        border_color=None,
        padding=12,
        font=None,
        key=None,
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        justification=None,
        right_click_menu=None,
        metadata=None,
    ):
        super().__init__(
            layout=layout,
            key=key,
            size=size,
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            justification=justification,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        if extra is not None and not isinstance(extra, Element):
            raise TypeError("extra must be an Element")
        self._title = None if title is None else str(title)
        self._subtitle = None if subtitle is None else str(subtitle)
        self._extra = extra
        self._background_color = background_color
        self._border_color = border_color
        self._padding = max(0, int(padding))
        self._font = font
        self._header = None
        self._header_text = None
        self._title_label = None
        self._subtitle_label = None
        self._separator = None
        self._body = None

    @property
    def title(self):
        """The header title (``None`` when the card has no title)."""
        return self._title

    @property
    def subtitle(self):
        """The secondary header line (``None`` when absent)."""
        return self._subtitle

    # --- widget construction ---------------------------------------------------
    def _create_widget(self, master):
        colors = _paint.palette(master, self._background_color)
        border = self._border_color or colors["border"]
        outer = tk.Frame(
            master,
            background=colors["surface"],
            highlightthickness=1,
            highlightbackground=border,
            bd=0,
        )
        if self._size and self._size[0]:
            outer.configure(width=int(self._size[0]))
        outer.columnconfigure(0, weight=1)
        # the body row absorbs slack when the card is asked to expand
        outer.rowconfigure(2, weight=1)
        header = tk.Frame(outer, background=colors["surface"])
        header.columnconfigure(0, weight=1)
        text_block = tk.Frame(header, background=colors["surface"])
        text_block.grid(row=0, column=0, sticky="w")
        title_font = self._font if self._font is not None else ("TkDefaultFont", 10, "bold")
        self._title_label = ttk.Label(
            text_block,
            text=self._title or "",
            foreground=colors["ink"],
            background=colors["surface"],
            anchor="w",
            font=title_font,
        )
        self._subtitle_label = ttk.Label(
            text_block,
            text=self._subtitle or "",
            foreground=colors["muted"],
            background=colors["surface"],
            anchor="w",
            font=("TkDefaultFont", 9),
        )
        self._header = header
        self._header_text = text_block
        self._separator = tk.Frame(outer, background=border, height=1, bd=0)
        self._body = tk.Frame(outer, background=colors["surface"])
        return outer

    def _post_create(self):
        # NOTE: skip ContainerElement._post_create -- it would build the
        # layout into the outermost frame; the body frame owns the content
        Element._post_create(self)
        header, body = self._header, self._body
        if header is None or body is None:
            return
        if self._layout:
            self._window._build_layout(self._layout, body)
        if self._extra is not None:
            self._window._register_element(self._extra)
            self._extra._build(header, self._window)
            # the extra hugs the header's right edge unless it says otherwise
            self._extra._grid_into(
                header, 0, 1, settings_mod.settings.element_padding, "right"
            )
        self._sync_header()

    def _sync_header(self):
        """Grid the header/separator/body rows for the current header state."""
        header, separator, body = self._header, self._separator, self._body
        title_label, subtitle_label = self._title_label, self._subtitle_label
        if header is None or separator is None or body is None:
            return
        if title_label is None or subtitle_label is None:
            return
        padding = self._padding
        has_header = bool(self._title) or bool(self._subtitle) or self._extra is not None
        if has_header:
            header.grid(row=0, column=0, sticky="we", padx=padding, pady=padding)
            separator.grid(row=1, column=0, sticky="we", pady=(0, padding))
            body.grid(row=2, column=0, sticky="nsew", padx=padding, pady=(0, padding))
        else:
            # an empty grid row collapses, so the body keeps the whole card
            header.grid_remove()
            separator.grid_remove()
            body.grid(row=2, column=0, sticky="nsew", padx=padding, pady=padding)
        if self._title:
            title_label.grid(row=0, column=0, sticky="w")
        else:
            title_label.grid_remove()
        if self._subtitle:
            subtitle_label.grid(row=1, column=0, sticky="w")
        else:
            subtitle_label.grid_remove()

    # --- user API --------------------------------------------------------------
    def get(self):
        """The card title."""
        return self._title

    def update(self, title=None, subtitle=None, visible=None):
        """Set the header texts (``None`` leaves a value unchanged)."""
        if title is not None:
            self._title = str(title)
            if self._title_label is not None:
                self._title_label.configure(text=self._title)
        if subtitle is not None:
            self._subtitle = str(subtitle)
            if self._subtitle_label is not None:
                self._subtitle_label.configure(text=self._subtitle)
        if title is not None or subtitle is not None:
            self._sync_header()
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self

    def apply_theme(self):
        """Repaint the outline, the layered surfaces and the header labels."""
        if self._widget is None:
            return self
        colors = _paint.palette(self._widget, self._background_color)
        border = self._border_color or colors["border"]
        self._widget.configure(
            background=colors["surface"], highlightbackground=border
        )
        for frame in (self._header, self._header_text, self._body):
            if frame is not None:
                frame.configure(background=colors["surface"])
        if self._separator is not None:
            self._separator.configure(background=border)
        if self._title_label is not None:
            self._title_label.configure(
                foreground=colors["ink"], background=colors["surface"]
            )
        if self._subtitle_label is not None:
            self._subtitle_label.configure(
                foreground=colors["muted"], background=colors["surface"]
            )
        return self


class Descriptions(Element):
    """An aligned label/value list.

    ``items`` is a ``[(label, value), ...]`` list or a dict (ordered on
    3.7+); ``columns`` spreads the pairs over that many grid columns.
    ``bordered=True`` wraps the block in a 1px outline::

        ts.Descriptions(
            [("Host", "10.0.0.7"), ("Port", 8080)],
            columns=2,
            bordered=True,
            label_suffix=":",
        )

    ``get()`` returns ``{label: value}`` with the values as they were given.
    """

    __slots__ = (
        "_items",
        "_columns",
        "_bordered",
        "_label_width",
        "_label_suffix",
        "_font",
        "_label_color",
        "_text_color",
        "_label_widgets",
        "_value_widgets",
    )

    def __init__(
        self,
        items,
        columns=2,
        bordered=False,
        label_width=None,
        label_suffix="",
        font=None,
        label_color=None,
        text_color=None,
        size=(None, None),
        key=None,
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        justification=None,
        right_click_menu=None,
        metadata=None,
    ):
        super().__init__(
            key=key,
            size=size,
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            justification=justification,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._items = _parse_descriptions(items)
        self._columns = max(1, int(columns))
        self._bordered = bool(bordered)
        self._label_width = label_width
        self._label_suffix = "" if label_suffix is None else str(label_suffix)
        self._font = font
        self._label_color = label_color
        self._text_color = text_color
        self._label_widgets: List[ttk.Label] = []
        self._value_widgets: List[ttk.Label] = []

    @property
    def items(self):
        """The (label, value) pairs currently displayed."""
        return list(self._items)

    def _create_widget(self, master):
        colors = _paint.palette(master)
        frame = tk.Frame(
            master,
            background=colors["surface"],
            highlightthickness=1 if self._bordered else 0,
            highlightbackground=colors["border"],
            bd=0,
        )
        self._populate(frame, colors)
        return frame

    def _populate(self, frame, colors: _paint.ColorMap):
        """(Re)create the label/value grid cells inside ``frame``."""
        self._label_widgets = []
        self._value_widgets = []
        label_fg = self._label_color or colors["muted"]
        value_fg = self._text_color or colors["ink"]
        if self._bordered:
            label_padx = (10, 10)
            value_padx = (10, 10)
            pady = 6
        else:
            # a 12px gap between a label and its value
            label_padx = (0, 0)
            value_padx = (12, 12)
            pady = 2
        for index, (label, value) in enumerate(self._items):
            row = index // self._columns
            pair = index % self._columns
            label_widget = ttk.Label(
                frame,
                text=label + self._label_suffix,
                foreground=label_fg,
                background=colors["surface"],
                anchor="w",
            )
            value_widget = ttk.Label(
                frame,
                text=_as_text(value),
                foreground=value_fg,
                background=colors["surface"],
                anchor="w",
            )
            if self._font is not None:
                label_widget.configure(font=self._font)
                value_widget.configure(font=self._font)
            if self._label_width is not None:
                label_widget.configure(width=int(self._label_width))
            label_widget.grid(
                row=row, column=pair * 2, sticky="w", padx=label_padx, pady=pady
            )
            value_widget.grid(
                row=row, column=pair * 2 + 1, sticky="w", padx=value_padx, pady=pady
            )
            self._label_widgets.append(label_widget)
            self._value_widgets.append(value_widget)

    def _rebuild(self):
        """Drop the cells and layout the current items again."""
        if self._widget is None:
            return
        for child in self._widget.winfo_children():
            child.destroy()
        self._populate(self._widget, _paint.palette(self._widget))

    def get(self):
        """``{label: value}`` for the current rows (values as passed in)."""
        return dict(self._items)

    def update(self, items=None, visible=None):
        """Replace the rows with ``items`` (``None`` keeps them)."""
        if items is not None:
            self._items = _parse_descriptions(items)
            self._rebuild()
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self

    def apply_theme(self):
        """Repaint the frame and every label from the active palette."""
        if self._widget is None:
            return self
        colors = _paint.palette(self._widget)
        label_fg = self._label_color or colors["muted"]
        value_fg = self._text_color or colors["ink"]
        self._widget.configure(
            background=colors["surface"], highlightbackground=colors["border"]
        )
        for widget in self._label_widgets:
            widget.configure(foreground=label_fg, background=colors["surface"])
        for widget in self._value_widgets:
            widget.configure(foreground=value_fg, background=colors["surface"])
        return self


class Steps(Element):
    """A step indicator drawn on a private canvas.

    ``items`` is a list of titles or ``(title, description)`` pairs.
    ``active`` marks the current step: every earlier step renders as
    finished (accent circle with a check mark), every later one as
    waiting. ``status`` styles the current step itself -- ``"process"``
    (default), ``"finish"``, ``"error"`` / ``"danger"`` or ``"wait"``::

        ts.Steps(["Cart", ("Address", "optional"), "Pay"], active=1,
                 key="-STEPS-")

    ``direction="vertical"`` stacks the steps instead of laying them out in
    a row. ``font`` overrides the title face only; descriptions stay small.
    """

    __slots__ = ("_items", "_active", "_direction", "_status", "_font")

    _DOT_RADIUS = 9.0     # 18px circles
    _DOT_Y = 16.0         # horizontal layout: circle centre line
    _TITLE_Y = 36.0       # horizontal layout: title, anchor "n"
    _DESC_Y = 52.0        # horizontal layout: description, anchor "n"
    _DOT_X = 10.0         # vertical layout: circle centre column
    _ROW_HEIGHT = 64.0    # vertical layout: row pitch
    _DEFAULT_WIDTH = 300  # vertical layout width without size[0]
    _DEFAULT_HEIGHT = 70  # horizontal layout height without size[1]
    _TITLE_FONT = ("TkDefaultFont", 9)
    _DESC_FONT = ("TkDefaultFont", 8)
    _NUMBER_FONT = ("TkDefaultFont", 8, "bold")

    def __init__(
        self,
        items,
        active=0,
        direction="horizontal",
        status="process",
        size=None,
        font=None,
        key=None,
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        justification=None,
        right_click_menu=None,
        metadata=None,
    ):
        if size is None:
            size = (None, None)
        super().__init__(
            key=key,
            size=size,
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            justification=justification,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._items = _parse_steps(items)
        self._active = int(active)
        self._direction = (
            "vertical"
            if str(direction).lower() in ("v", "vertical")
            else "horizontal"
        )
        self._status = str(status)
        self._font = font

    @property
    def active(self):
        """Index of the current step."""
        return self._active

    @property
    def direction(self):
        """``"horizontal"`` or ``"vertical"``."""
        return self._direction

    # --- geometry --------------------------------------------------------------
    def _geometry(self, master=None):
        """Canvas size in pixels (``master`` is only used to measure text)."""
        count = max(1, len(self._items))
        if self._direction == "vertical":
            width = self._size[0] or self._DEFAULT_WIDTH
            height = self._size[1] or int(count * self._ROW_HEIGHT)
            return int(width), int(height)
        width = self._size[0] or int(count * self._cell_width(master))
        height = self._size[1] or self._DEFAULT_HEIGHT
        return int(width), int(height)

    def _cell_width(self, master):
        """Horizontal cell width driven by the widest title/description."""
        widest = 0
        for title, description in self._items:
            widest = max(
                widest, _paint.measure_text(master, title, self._title_font())
            )
            if description:
                widest = max(
                    widest,
                    _paint.measure_text(master, description, self._DESC_FONT),
                )
        return max(96, widest + 28)

    def _title_font(self):
        return self._font if self._font is not None else self._TITLE_FONT

    # --- rendering -------------------------------------------------------------
    def _create_widget(self, master):
        width, height = self._geometry(master)
        colors = _paint.palette(master)
        canvas = _paint.themed_canvas(master, width, height, colors["surface"])
        self._draw(canvas)
        return canvas

    def _draw(self, canvas):
        """Redraw every figure from a freshly resolved palette."""
        colors = _paint.palette(canvas)
        canvas.configure(background=colors["surface"])
        canvas.delete("all")
        if self._direction == "vertical":
            self._draw_vertical(canvas, colors)
        else:
            self._draw_horizontal(canvas, colors)
        width, height = self._geometry(canvas)
        canvas.configure(width=width, height=height)

    def _draw_horizontal(self, canvas, colors: _paint.ColorMap):
        count = len(self._items)
        if not count:
            return
        width, _height = self._geometry(canvas)
        cell = width / float(count)
        centers = [cell * (index + 0.5) for index in range(count)]
        for index in range(count - 1):
            line_color = colors["accent"] if index < self._active else colors["track"]
            canvas.create_line(
                centers[index] + 11, self._DOT_Y,
                centers[index + 1] - 11, self._DOT_Y,
                fill=line_color, width=2,
            )
        for index, (title, description) in enumerate(self._items):
            state = self._state(index)
            self._draw_dot(canvas, centers[index], self._DOT_Y, index, state, colors)
            title_color = colors["ink"] if index <= self._active else colors["muted"]
            canvas.create_text(
                centers[index], self._TITLE_Y, text=title, anchor="n",
                fill=title_color, font=self._title_font(),
            )
            if description:
                canvas.create_text(
                    centers[index], self._DESC_Y, text=description, anchor="n",
                    fill=colors["muted"], font=self._DESC_FONT,
                    width=max(20, int(cell) - 10),
                )

    def _draw_vertical(self, canvas, colors: _paint.ColorMap):
        count = len(self._items)
        if not count:
            return
        width, _height = self._geometry(canvas)
        for index in range(count - 1):
            line_color = colors["accent"] if index < self._active else colors["track"]
            top = index * self._ROW_HEIGHT + 12
            canvas.create_line(
                self._DOT_X, top + 11,
                self._DOT_X, top + self._ROW_HEIGHT - 11,
                fill=line_color, width=2,
            )
        for index, (title, description) in enumerate(self._items):
            state = self._state(index)
            center_y = index * self._ROW_HEIGHT + 12
            self._draw_dot(canvas, self._DOT_X, center_y, index, state, colors)
            title_color = colors["ink"] if index <= self._active else colors["muted"]
            canvas.create_text(
                26, center_y - 2, text=title, anchor="w",
                fill=title_color, font=self._title_font(),
            )
            if description:
                canvas.create_text(
                    26, center_y + 16, text=description, anchor="w",
                    fill=colors["muted"], font=self._DESC_FONT,
                    width=max(20, width - 40),
                )

    def _state(self, index):
        """The circle style for a step: finish / process / danger / wait."""
        if index < self._active:
            return "finish"
        if index > self._active:
            return "wait"
        status = (self._status or "process").lower()
        if status in ("error", "danger"):
            return "danger"
        if status in ("finish", "success"):
            return "finish"
        if status in ("wait", "waiting"):
            return "wait"
        return "process"

    def _draw_dot(self, canvas, cx, cy, index, state, colors: _paint.ColorMap):
        radius = self._DOT_RADIUS
        box = (cx - radius, cy - radius, cx + radius, cy + radius)
        if state == "wait":
            canvas.create_oval(
                *box, fill=colors["surface"], outline=colors["track"], width=1.5
            )
            canvas.create_text(
                cx, cy, text=str(index + 1),
                fill=colors["muted"], font=self._NUMBER_FONT,
            )
            return
        if state == "danger":
            color = _paint.status_color("danger", colors)
            canvas.create_oval(*box, fill=color, outline="")
            _paint.cross(
                canvas, cx, cy, 8, fill=theme_mod.contrast_on(color), width=2
            )
            return
        canvas.create_oval(*box, fill=colors["accent"], outline="")
        if state == "finish":
            _paint.check_mark(
                canvas, cx, cy, 9, fill=colors["accent_ink"], width=2
            )
        else:
            canvas.create_text(
                cx, cy, text=str(index + 1),
                fill=colors["accent_ink"], font=self._NUMBER_FONT,
            )

    # --- user API ---------------------------------------------------------------
    def get(self):
        """Index of the current step."""
        return self._active

    def update(self, active=None, status=None, items=None, visible=None):
        """Move the current step, restyle it or replace the step list."""
        changed = items is not None or active is not None or status is not None
        if items is not None:
            self._items = _parse_steps(items)
        if active is not None:
            self._active = int(active)
        if status is not None:
            self._status = str(status)
        if changed and self._widget is not None:
            self._draw(self._widget)
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self

    def apply_theme(self):
        """Clear the canvas and redraw it with the new palette."""
        if self._widget is not None:
            self._draw(self._widget)
        return self


class Timeline(Element):
    """A vertical activity feed drawn on a private canvas.

    Every entry is one row; ``items`` accepts three forms::

        ts.Timeline([
            "Deployed",                                   # content only
            ("09:30", "Build finished"),                  # + timestamp
            {"timestamp": "10:00", "content": "Rollback",
             "type": "success", "color": None},           # + dot style
        ])

    The dot takes ``color`` when given, otherwise the semantic color of
    ``type`` ("primary" by default, plus info / success / warning / error).
    ``row_height`` sets the minimum row pitch (default 46 with a timestamp,
    30 without); wrapped content pushes the following rows down. ``size[0]``
    sets the width (default 320). Leave ``size[1]`` out to let the element
    grow with its content -- a fixed height clips longer feeds.
    """

    __slots__ = ("_items", "_row_height", "_font", "_line_color", "_auto_height")

    _DEFAULT_WIDTH = 320
    _DOT_X = 8.0
    _DOT_RADIUS = 3.5
    _TEXT_X = 20.0
    _TOP_PAD = 8.0
    _ROW_TIMESTAMP = 46.0
    _ROW_PLAIN = 30.0
    _TS_FONT = ("TkDefaultFont", 8)
    _CONTENT_FONT = ("TkDefaultFont", 9)

    def __init__(
        self,
        items,
        size=None,
        row_height=None,
        font=None,
        line_color=None,
        key=None,
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        justification=None,
        right_click_menu=None,
        metadata=None,
    ):
        if size is None:
            size = (None, None)
        super().__init__(
            key=key,
            size=size,
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            justification=justification,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._items = _parse_timeline(items)
        self._row_height = row_height
        self._font = font
        self._line_color = line_color
        self._auto_height = float(self._estimate_height())

    # --- geometry --------------------------------------------------------------
    def _geometry(self):
        """Canvas size in pixels (height follows the measured content)."""
        width = int(self._size[0] or self._DEFAULT_WIDTH)
        if self._size[1]:
            return width, int(self._size[1])
        return width, int(max(40.0, self._auto_height))

    def _item_height(self, has_timestamp):
        """Minimum row pitch for one entry."""
        if self._row_height is not None:
            return float(self._row_height)
        return self._ROW_TIMESTAMP if has_timestamp else self._ROW_PLAIN

    def _estimate_height(self):
        """Opening height guess; :meth:`_draw` replaces it with the measured one."""
        total = self._TOP_PAD
        for timestamp, _content, _kind, _color in self._items:
            total += self._item_height(_has_timestamp(timestamp))
        return int(max(40.0, total))

    # --- rendering -------------------------------------------------------------
    def _create_widget(self, master):
        width, height = self._geometry()
        colors = _paint.palette(master)
        canvas = _paint.themed_canvas(master, width, height, colors["surface"])
        self._draw(canvas)
        return canvas

    def _draw(self, canvas):
        """Redraw every figure from a freshly resolved palette."""
        colors = _paint.palette(canvas)
        canvas.configure(background=colors["surface"])
        canvas.delete("all")
        width, _height = self._geometry()
        line_color = self._line_color or colors["track"]
        content_font = self._font if self._font is not None else self._CONTENT_FONT
        dots: List[Tuple[float, str]] = []
        bottom = self._TOP_PAD
        y = self._TOP_PAD
        for timestamp, content, kind, color in self._items:
            if _has_timestamp(timestamp):
                canvas.create_text(
                    self._TEXT_X, y, text=str(timestamp), anchor="nw",
                    fill=colors["muted"], font=self._TS_FONT,
                )
                content_y = y + 14
            else:
                content_y = y
            row_bottom = float(content_y)
            if content:
                content_id = canvas.create_text(
                    self._TEXT_X, content_y, text=content, anchor="nw",
                    fill=colors["ink"], font=content_font,
                    width=max(20, width - 40),
                )
                box = canvas.bbox(content_id)
                if box is not None:
                    row_bottom = float(box[3])
            dots.append((y + 6.0, color or _paint.status_color(kind or "primary", colors)))
            bottom = row_bottom
            y = max(y + self._item_height(_has_timestamp(timestamp)), row_bottom + 8.0)
        if len(dots) > 1:
            canvas.create_line(
                self._DOT_X, dots[0][0], self._DOT_X, dots[-1][0],
                fill=line_color, width=1.5,
            )
        for center_y, dot_color in dots:
            canvas.create_oval(
                self._DOT_X - self._DOT_RADIUS, center_y - self._DOT_RADIUS,
                self._DOT_X + self._DOT_RADIUS, center_y + self._DOT_RADIUS,
                fill=dot_color, outline="",
            )
        self._auto_height = max(40.0, bottom + 8.0)
        width, height = self._geometry()
        canvas.configure(width=width, height=height)

    # --- user API ---------------------------------------------------------------
    def get(self):
        """The ``(timestamp, content)`` pairs (timestamp is ``None`` if absent)."""
        return [(timestamp, content) for timestamp, content, _kind, _color in self._items]

    def update(self, items=None, visible=None):
        """Replace the entries with ``items`` (``None`` keeps them)."""
        if items is not None:
            self._items = _parse_timeline(items)
            self._auto_height = float(self._estimate_height())
            if self._widget is not None:
                self._draw(self._widget)
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self

    def apply_theme(self):
        """Clear the canvas and redraw it with the new palette."""
        if self._widget is not None:
            self._draw(self._widget)
        return self
