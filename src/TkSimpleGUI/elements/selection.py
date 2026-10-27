#!/usr/bin/env python3
"""Selection and rating widgets.

- :class:`TSegmented`  -- segmented control (pill track, hover, arrow keys)
- :class:`TRate`       -- star rating with hover preview and half stars
- :class:`TPagination` -- pager with a sliding window of page buttons
- :class:`TTransfer`   -- two listboxes with arrows moving items between them

TSegmented, TRate and TPagination paint themselves on a flat canvas: the
``_geometry`` helper reports the canvas size, ``_draw`` repaints every
figure from a freshly resolved palette, and ``apply_theme`` is that same
repaint. TTransfer composes plain Tk widgets and refreshes their colors in
``apply_theme``. Only real state changes post an event.
"""

import math
import tkinter as tk
from functools import partial
from tkinter import ttk
from typing import Any, List, Optional, Sequence, Tuple, Union

from . import _paint
from .base import Element, ElementKey, FontSpec, MenuDefinition, PadSpec, Size
from .. import _theming as theme_mod

# canvas elements measure text with the font they draw it with, so the
# computed pixel widths agree on every platform (Tk's real default font
# differs between systems)
_DEFAULT_FONT = ("TkDefaultFont", 10)

# glyphs written as escapes so this module stays pure ASCII
_CHEVRON_LEFT = "\u2039"   # "‹" previous page / move selection left
_CHEVRON_RIGHT = "\u203a"  # "›" next page / move selection right
_DOUBLE_LEFT = "\u00ab"    # "«" move everything left
_DOUBLE_RIGHT = "\u00bb"   # "»" move everything right
_PAGE_ELLIPSIS = "\u2026"  # "…" page numbers skipped by the window


def _segmented_options(options: Sequence[Any]):
    """Normalize ``["A", "B"]`` / ``[("A", 1), ("B", 2)]`` to (label, value)."""
    pairs: List[Tuple[str, Any]] = []
    for option in options or ():
        if isinstance(option, (list, tuple)):
            if len(option) != 2:
                raise ValueError("options must hold labels or (label, value) pairs")
            pairs.append((str(option[0]), option[1]))
        else:
            pairs.append((str(option), option))
    return pairs


class TSegmented(Element):
    """A segmented control: one pill per option, exactly one selected.

    ``options`` is a list of labels or of ``(label, value)`` pairs; the
    selected option's *value* is what :meth:`get` returns::

        ts.TSegmented(["Day", "Week", "Month"], default_value="Week", key="-SEG-")

    Clicking a segment selects it (a changed selection posts the key);
    ``readonly=True`` makes the control display-only. The canvas takes
    keyboard focus, so the arrow keys move the selection as well.
    """

    __slots__ = (
        "_options",
        "_index",
        "_font",
        "_enable_events",
        "_readonly",
        "_hover",
        "_focused",
        "_cells",
    )

    # None: no option selected (empty options) / nothing hovered
    _index: Optional[int]
    _hover: Optional[int]
    _cells: List[Tuple[float, float]]

    def __init__(
        self,
        options: Sequence[Any],
        default_value: Any = None,
        size: Optional[Size] = None,
        font: Optional[FontSpec] = None,
        key: Optional[ElementKey] = None,
        enable_events: bool = True,
        readonly: bool = False,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            size=size if size is not None else (None, None),
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._options = _segmented_options(options)
        index = self._find_index(default_value)
        self._index = index if index is not None else (0 if self._options else None)
        self._font = font
        self._enable_events = bool(enable_events)
        self._readonly = bool(readonly)
        self._hover = None
        self._focused = False
        self._cells = []

    # --- state ---------------------------------------------------------------
    def _find_index(self, value: Any):
        """The index of the option carrying ``value`` (None when absent)."""
        for index, (_label, option_value) in enumerate(self._options):
            if option_value == value:
                return index
        return None

    def get(self):
        """The value of the selected segment (None when there are no options)."""
        if self._index is None:
            return None
        return self._options[self._index][1]

    # --- geometry ------------------------------------------------------------
    def _item_width(self, widget: tk.Misc, label: str):
        """Pixel width of one segment: label + 24, never under 40."""
        font = self._font if self._font is not None else _DEFAULT_FONT
        return max(40, _paint.measure_text(widget, label, font) + 24)

    def _layout(self, widget: Optional[tk.Misc] = None):
        """(cells, total width): the x range of every segment inside the track."""
        root = widget if widget is not None else self._widget
        widths = [float(self._item_width(root, label)) for label, _value in self._options]
        total = sum(widths) + 4.0
        if self._size[0]:
            # an explicit width stretches every cell proportionally to fill it
            wanted = max(4.0, float(self._size[0]))
            base = sum(widths)
            if base > 0:
                scale = (wanted - 4.0) / base
                widths = [width * scale for width in widths]
            total = wanted
        cells: List[Tuple[float, float]] = []
        left = 2.0
        for width in widths:
            cells.append((left, left + width))
            left += width
        return cells, total

    def _geometry(self, widget: Optional[tk.Misc] = None):
        """(width, height) of the segmented track in pixels."""
        _cells, total = self._layout(widget)
        return int(total), int(self._size[1] or 30)

    def _redraw(self):
        """Repaint an existing canvas (a no-op before finalization)."""
        if self._widget is not None:
            self._draw(self._widget)

    # --- rendering -----------------------------------------------------------
    def _create_widget(self, master: tk.Misc):
        width, height = self._geometry(master)
        colors = _paint.palette(master)
        canvas = _paint.themed_canvas(master, width, height, colors["surface"])
        canvas.configure(takefocus=1)  # arrow keys move the selection
        self._draw(canvas)
        return canvas

    def _draw(self, canvas: tk.Canvas):
        """Draw the track, the selected pill and every label."""
        colors = _paint.palette(canvas)
        canvas.configure(background=colors["surface"])
        canvas.delete("all")
        self._cells, total = self._layout(canvas)
        height = int(self._size[1] or 30)
        _paint.capsule(
            canvas, 1, 1, total - 1, height - 1,
            fill=colors["subtle"], outline=colors["border"], width=1,
        )
        for index, (label, _value) in enumerate(self._options):
            left, right = self._cells[index]
            self._draw_segment(canvas, index, label, left, right, height, colors)

    def _draw_segment(
        self,
        canvas: tk.Canvas,
        index: int,
        label: str,
        left: Any,
        right: Any,
        height: int,
        colors: _paint.ColorMap):
        """One segment: selected pill, label and (when focused) the focus ring."""
        selected = index == self._index
        if selected:
            _paint.capsule(
                canvas, left + 2, 2, right - 2, height - 2,
                fill=colors["accent"], outline="",
            )
            fill = colors["accent_ink"]
        elif index == self._hover:
            fill = colors["accent"]
        else:
            fill = colors["ink"]
        canvas.create_text(
            (left + right) / 2.0,
            height / 2.0,
            text=label,
            fill=fill,
            font=self._font if self._font is not None else _DEFAULT_FONT,
        )
        if selected and self._focused:
            _paint.rounded_polygon(
                canvas, left + 1, 1, right - 1, height - 1, (height - 2) / 2.0,
                fill="", outline=colors["accent"], width=1,
            )

    def apply_theme(self):
        """Repaint the track, pills and labels for the active theme."""
        self._redraw()
        return self

    # --- interaction ---------------------------------------------------------
    def _index_at(self, x: float):
        """The segment index covering ``x`` (None in the track margin)."""
        for index, (left, right) in enumerate(self._cells):
            if left <= x <= right:
                return index
        return None

    def _on_click(self, event: tk.Event):
        if self._readonly:
            return
        index = self._index_at(event.x)
        if index is None:
            return
        was_focused = self._focused
        self._focused = True
        self._widget.focus_set()
        if index != self._index:
            self._index = index
            self._redraw()
            if self._enable_events:
                self._post_event()
        elif not was_focused:
            self._redraw()

    def _on_motion(self, event: tk.Event):
        if self._readonly:
            return
        index = self._index_at(event.x)
        if index != self._hover:
            self._hover = index
            self._redraw()

    def _on_leave(self, _event: tk.Event):
        if self._hover is not None:
            self._hover = None
            self._redraw()

    def _on_focus_in(self, _event: tk.Event):
        if not self._focused:
            self._focused = True
            self._redraw()

    def _on_focus_out(self, _event: tk.Event):
        if self._focused:
            self._focused = False
            self._redraw()

    def _on_arrow(self, step: int, _event: tk.Event):
        """Move the selection by ``step`` segments (Left / Right key)."""
        if self._readonly or not self._options:
            return
        index = 0 if self._index is None else self._index + step
        index = min(max(index, 0), len(self._options) - 1)
        if index != self._index:
            self._index = index
            self._redraw()
            if self._enable_events:
                self._post_event()

    def _bind_events(self):
        self._widget.bind("<Button-1>", self._on_click)
        self._widget.bind("<Motion>", self._on_motion)
        self._widget.bind("<Leave>", self._on_leave)
        self._widget.bind("<FocusIn>", self._on_focus_in)
        self._widget.bind("<FocusOut>", self._on_focus_out)
        self._widget.bind("<Left>", partial(self._on_arrow, -1))
        self._widget.bind("<Right>", partial(self._on_arrow, 1))

    # --- public API ----------------------------------------------------------
    def update(
        self,
        value: Any = None,
        options: Optional[Sequence[Any]] = None,
        visible: Optional[bool] = None):
        """Change the selection, rebuild the options or toggle visibility.

        Rebuilding keeps the current value when it is still offered, and
        otherwise selects the first option.
        """
        redraw = options is not None or value is not None
        if options is not None:
            current = self.get()
            self._options = _segmented_options(options)
            index = self._find_index(current)
            self._index = index if index is not None else (0 if self._options else None)
            self._hover = None
        if value is not None:
            index = self._find_index(value)
            if index is not None:
                self._index = index
        if redraw:
            self._redraw()
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class TRate(Element):
    """A star rating with hover preview and optional half stars.

    ``max_value`` stars are drawn; clicking one sets the value and moving
    the pointer over the stars previews the value a click would apply.
    With ``allow_half`` (the default) the left half of a star selects
    ``n - 0.5`` -- the first star's left half is 0.5, there is no "clear"
    gesture::

        ts.TRate(max_value=5, default_value=3.5, key="-RATE-")
    """

    __slots__ = (
        "_max_value",
        "_value",
        "_allow_half",
        "_colors",
        "_font",
        "_enable_events",
        "_readonly",
        "_hover",
        "_star_size",
        "_step",
    )

    # None: no hover preview in progress
    _hover: Optional[float]
    _colors: Optional[Tuple[str, str]]

    def __init__(
        self,
        max_value: float = 5,
        default_value: Any = 0,
        allow_half: bool = True,
        size: Optional[Size] = None,
        colors: Any = None,
        font: Optional[FontSpec] = None,
        key: Optional[ElementKey] = None,
        enable_events: bool = True,
        readonly: bool = False,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            size=size if size is not None else (None, None),
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        if colors is not None and len(colors) != 2:
            raise ValueError("colors must be a (filled, empty) pair")
        self._max_value = max(1, int(max_value))
        self._allow_half = bool(allow_half)
        self._colors = None if colors is None else (str(colors[0]), str(colors[1]))
        # ``font`` is accepted for constructor symmetry; the stars carry no text
        self._font = font
        self._enable_events = bool(enable_events)
        self._readonly = bool(readonly)
        self._hover = None
        self._star_size = float(self._size[1] or 26)
        self._step = self._star_size * 1.28  # star size + 28% gap
        self._value = self._clamp(default_value)

    # --- state ---------------------------------------------------------------
    def _clamp(self, value: Any):
        """Quantize to the allowed step and clamp into [0, max_value]."""
        number = _paint.as_float(value, 0.0)
        number = (
            int(number * 2.0 + 0.5) / 2.0 if self._allow_half else float(int(number + 0.5))
        )
        return min(max(number, 0.0), float(self._max_value))

    def _value_at(self, x: float):
        """The value a click at ``x`` would select (half stars when allowed)."""
        index = min(max(int(x / self._step) + 1, 1), self._max_value)
        if self._allow_half and x - (index - 1) * self._step < self._star_size / 2.0:
            return index - 0.5
        return float(index)

    # --- geometry ------------------------------------------------------------
    def _geometry(self):
        """(width, height) of the star row in pixels."""
        gap = self._step - self._star_size
        return int(self._max_value * self._step - gap), int(self._star_size)

    def _redraw(self):
        """Repaint an existing canvas (a no-op before finalization)."""
        if self._widget is not None:
            self._draw(self._widget)

    # --- rendering -----------------------------------------------------------
    def _create_widget(self, master: tk.Misc):
        width, height = self._geometry()
        colors = _paint.palette(master)
        canvas = _paint.themed_canvas(master, width, height, colors["surface"])
        self._draw(canvas)
        return canvas

    def _draw(self, canvas: tk.Canvas):
        """Draw every star for the current value (or the hover preview)."""
        colors = _paint.palette(canvas)
        canvas.configure(background=colors["surface"])
        canvas.delete("all")
        if self._colors is not None:
            filled, empty = self._colors
        else:
            filled, empty = "#f7ba2a", colors["track"]
        shown = self._value if self._hover is None else self._hover
        radius = self._star_size / 2.0
        inner = radius * 0.42
        for index in range(self._max_value):
            cx = index * self._step + radius
            points = _paint.star_points(cx, radius, radius, inner)
            self._draw_star(canvas, points, shown - index, filled, empty)

    def _draw_star(
        self,
        canvas: tk.Canvas,
        points: Sequence[Tuple[float, float]],
        fraction: Any,
        filled: Any,
        empty: Any):
        """One star: filled, empty, or the clipped left half of a half star."""
        if fraction >= 1.0:
            canvas.create_polygon(_paint.flatten(points), fill=filled, outline="")
            return
        canvas.create_polygon(_paint.flatten(points), fill=empty, outline="")
        if fraction > 0.0:
            # the Sutherland-Hodgman clip keeps exactly the left half
            half = _paint.flatten(_paint.clip_left_half(points))
            canvas.create_polygon(half, fill=filled, outline="")

    def apply_theme(self):
        """Repaint the stars for the active theme (explicit colors win)."""
        self._redraw()
        return self

    # --- interaction ---------------------------------------------------------
    def _on_click(self, event: tk.Event):
        if self._readonly:
            return
        value = self._value_at(event.x)
        if value != self._value:
            self._value = value
            self._redraw()
            if self._enable_events:
                self._post_event()

    def _on_motion(self, event: tk.Event):
        if self._readonly:
            return
        value = self._value_at(event.x)
        if value != self._hover:
            self._hover = value
            self._redraw()

    def _on_leave(self, _event: tk.Event):
        if self._hover is not None:
            self._hover = None
            self._redraw()

    def _on_key(self, event: tk.Event):
        """Keyboard parity for the rating: Left/Right step by 1, Home/End
        jump to the ends, 0 clears. Each press posts a TkSimpleEvent only
        if the value actually changed (mirrors the click handler)."""
        if self._readonly:
            return "break"
        symbol = getattr(event, "keysym", "")
        if symbol == "Left":
            step = -1
        elif symbol == "Right":
            step = 1
        elif symbol == "Home":
            step = -(self._max_value)
        elif symbol == "End":
            step = self._max_value
        elif symbol in ("0", "BackSpace"):
            new = 0
            if new == self._value:
                return "break"
            self._value = new
            self._redraw()
            if self._enable_events:
                self._post_event()
            return "break"
        else:
            return None
        new = max(0, min(self._max_value, int(round(self._value)) + step))
        if new == self._value:
            return "break"
        self._value = float(new)
        self._redraw()
        if self._enable_events:
            self._post_event()
        return "break"

    def _bind_events(self):
        self._widget.bind("<Button-1>", self._on_click)
        self._widget.bind("<Motion>", self._on_motion)
        self._widget.bind("<Key>", self._on_key)
        # the canvas must take focus for key events to reach it
        self._widget.bind("<Button-1>", lambda _e: self._widget.focus_set(), add="+")
        self._widget.bind("<Leave>", self._on_leave)

    # --- public API ----------------------------------------------------------
    def get(self):
        """The rating as a float (0 means "not rated")."""
        return self._value

    def update(
        self,
        value: Any = None,
        max_value: Optional[float] = None,
        readonly: Optional[bool] = None,
        visible: Optional[bool] = None):
        """Set the rating, the star count, the read-only flag or visibility."""
        redraw = False
        if max_value is not None:
            self._max_value = max(1, int(max_value))
            self._value = min(self._value, float(self._max_value))
            redraw = True
        if value is not None:
            self._value = self._clamp(value)
            redraw = True
        if readonly is not None:
            self._readonly = bool(readonly)
            if self._readonly:
                self._hover = None
            redraw = True
        if redraw:
            self._redraw()
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class TPagination(Element):
    """A pager: prev/next chevrons around a window of page buttons.

    ``page_count`` is ``ceil(total / page_size)``, never below 1. When more
    pages exist than ``pager_count`` the row shows the pages around the
    current one between the fixed first and last page, with "…" wherever
    pages are skipped::

        ts.TPagination(total=95, page_size=10, current_page=3, key="-PAG-")

    Clicking a button (or a chevron) changes the page; the change posts the
    key and ``values[key]`` is the current page number.
    """

    __slots__ = (
        "_total",
        "_page_size",
        "_current_page",
        "_pager_count",
        "_show_total",
        "_total_text",
        "_font",
        "_enable_events",
        "_hover",
        "_boxes",
    )

    # None: no hovered button
    _hover: Optional[int]
    _boxes: List[Tuple[float, float, float, float, Union[int, str]]]

    def __init__(
        self,
        total: Any,
        page_size: int = 10,
        current_page: int = 1,
        pager_count: int = 5,
        show_total: bool = False,
        total_text: str = "Total {total}",
        size: Optional[Size] = None,
        font: Optional[FontSpec] = None,
        key: Optional[ElementKey] = None,
        enable_events: bool = True,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            size=size if size is not None else (None, None),
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        if int(total) < 0:
            raise ValueError("total must be zero or greater")
        if int(page_size) < 1:
            raise ValueError("page_size must be at least 1")
        self._total = int(total)
        self._page_size = int(page_size)
        self._pager_count = max(3, int(pager_count))
        self._show_total = bool(show_total)
        self._total_text = str(total_text)
        self._font = font
        self._enable_events = bool(enable_events)
        self._hover = None
        self._boxes = []
        self._current_page = self._clamp_page(int(current_page))

    # --- state ---------------------------------------------------------------
    @property
    def page_count(self):
        """The number of pages (``ceil(total / page_size)``, minimum 1)."""
        return max(1, int(math.ceil(self._total / float(self._page_size))))

    def _clamp_page(self, page: int):
        """Clamp a page number into ``[1, page_count]``."""
        return min(max(int(page), 1), self.page_count)

    def _page_window(self):
        """The page numbers to show, with "…" wherever pages are skipped."""
        count = self.page_count
        if count <= self._pager_count:
            return list(range(1, count + 1))
        # the window holds pager_count - 2 pages, centred on the current one
        # but never covering page 2's left neighbour or the last page
        start = self._current_page - (self._pager_count - 3) // 2
        start = min(max(start, 2), count - (self._pager_count - 2))
        end = start + self._pager_count - 2  # first page after the window
        items: List[Union[int, str]] = [1]
        if start > 2:
            # one skipped page is shown directly, several collapse to "…"
            items.append(_PAGE_ELLIPSIS if start > 3 else start - 1)
        items.extend(range(start, end))
        if end < count - 1:
            items.append(_PAGE_ELLIPSIS)
        elif end == count - 1:
            items.append(end)
        items.append(count)
        return items

    def _entries(self):
        """Every box value, left to right: prev chevron, pages, next chevron."""
        entries: List[Union[int, str]] = ["prev"]
        entries.extend(self._page_window())
        entries.append("next")
        return entries

    def _entry_label(self, entry: Any):
        """The label drawn inside one button box."""
        if entry == "prev":
            return _CHEVRON_LEFT
        if entry == "next":
            return _CHEVRON_RIGHT
        return str(entry)

    def _step_target(self, entry: Any):
        """The page a click on ``entry`` goes to (the current page when inert)."""
        if isinstance(entry, int):
            return entry
        if entry == "prev":
            return self._current_page - 1
        if entry == "next":
            return self._current_page + 1
        return self._current_page

    def _is_active(self, entry: Any):
        """True when clicking ``entry`` would turn to another page."""
        return self._step_target(entry) != self._current_page

    # --- geometry ------------------------------------------------------------
    def _layout(self, widget: Optional[tk.Misc] = None):
        """(boxes, width, total x): the button boxes and the row width."""
        root = widget if widget is not None else self._widget
        font = self._font if self._font is not None else _DEFAULT_FONT
        height = float(self._size[1] or 28)
        total_x = None
        x = 0.0
        if self._show_total:
            total_x = 0.0
            x = float(_paint.measure_text(root, self._total_text.format(total=self._total), font))
            x += 12.0
        boxes: List[Tuple[float, float, float, float, Union[int, str]]] = []
        for entry in self._entries():
            width = max(28.0, float(_paint.measure_text(root, self._entry_label(entry), font) + 16))
            boxes.append((x, 0.0, x + width, height, entry))
            x += width + 4.0
        width = x - 4.0 if boxes else 0.0
        if self._size[0]:
            # an explicit width may add trailing room; buttons are never clipped
            width = max(width, float(self._size[0]))
        return boxes, width, total_x

    def _geometry(self, widget: Optional[tk.Misc] = None):
        """(width, height) of the pager row in pixels."""
        _boxes, width, _total_x = self._layout(widget)
        return int(width), int(self._size[1] or 28)

    def _redraw(self):
        """Repaint an existing canvas (a no-op before finalization)."""
        if self._widget is not None:
            self._draw(self._widget)

    # --- rendering -----------------------------------------------------------
    def _create_widget(self, master: tk.Misc):
        width, height = self._geometry(master)
        colors = _paint.palette(master)
        canvas = _paint.themed_canvas(master, width, height, colors["surface"])
        self._draw(canvas)
        return canvas

    def _draw(self, canvas: tk.Canvas):
        """Draw the optional total label and every page button."""
        colors = _paint.palette(canvas)
        canvas.configure(background=colors["surface"])
        canvas.delete("all")
        self._boxes, _width, total_x = self._layout(canvas)
        height = int(self._size[1] or 28)
        font = self._font if self._font is not None else _DEFAULT_FONT
        if total_x is not None:
            canvas.create_text(
                total_x, height / 2.0, text=self._total_text.format(total=self._total),
                anchor="w", fill=colors["muted"], font=font,
            )
        for index, box in enumerate(self._boxes):
            self._draw_button(canvas, index, box, colors, font)

    def _draw_button(
        self,
        canvas: tk.Canvas,
        index: int,
        box: Any,
        colors: _paint.ColorMap,
        font: Optional[FontSpec]):
        """One page button: pill when current or hovered, label otherwise."""
        left, top, right, bottom, entry = box
        page = isinstance(entry, int)
        if page and entry == self._current_page:
            _paint.capsule(
                canvas, left + 2, top + 2, right - 2, bottom - 2,
                fill=colors["accent"], outline="",
            )
            fill = colors["accent_ink"]
        elif page or self._is_active(entry):
            fill = colors["ink"]
            if index == self._hover:
                _paint.capsule(
                    canvas, left + 2, top + 2, right - 2, bottom - 2,
                    fill=colors["subtle"], outline="",
                )
        else:
            fill = colors["muted"]  # ellipsis and disabled chevrons
        canvas.create_text(
            (left + right) / 2.0, (top + bottom) / 2.0,
            text=self._entry_label(entry), fill=fill, font=font,  # ty: ignore[invalid-argument-type]  tk accepts font tuples
        )

    def apply_theme(self):
        """Repaint the pager for the active theme."""
        self._redraw()
        return self

    # --- interaction ---------------------------------------------------------
    def _button_at(self, x: float, y: float):
        """The index of the button box under (x, y), or None."""
        for index, (left, top, right, bottom, _entry) in enumerate(self._boxes):
            if left <= x <= right and top <= y <= bottom:
                return index
        return None

    def _goto(self, page: int):
        """Turn to ``page`` and post the key when it really changed."""
        page = self._clamp_page(page)
        if page == self._current_page:
            return
        self._current_page = page
        self._redraw()
        if self._enable_events:
            self._post_event()

    def _on_click(self, event: tk.Event):
        index = self._button_at(event.x, event.y)
        if index is None:
            return
        self._goto(self._step_target(self._boxes[index][4]))

    def _on_motion(self, event: tk.Event):
        index = self._button_at(event.x, event.y)
        if index is not None and not self._is_active(self._boxes[index][4]):
            index = None
        if index != self._hover:
            self._hover = index
            self._redraw()

    def _on_leave(self, _event: tk.Event):
        if self._hover is not None:
            self._hover = None
            self._redraw()

    def _on_key(self, event: tk.Event):
        """Keyboard parity for the pager: Left/Right move one page,
        Home/End jump to the first/last page. Posts the key only when the
        page actually changes (mirrors :meth:`_goto`)."""
        symbol = getattr(event, "keysym", "")
        if symbol == "Left":
            self._goto(self._current_page - 1)
            return "break"
        if symbol == "Right":
            self._goto(self._current_page + 1)
            return "break"
        if symbol == "Home":
            self._goto(1)
            return "break"
        if symbol == "End":
            self._goto(self.page_count)
            return "break"
        return None

    def _bind_events(self):
        self._widget.bind("<Button-1>", self._on_click)
        self._widget.bind("<Motion>", self._on_motion)
        self._widget.bind("<Leave>", self._on_leave)
        self._widget.bind("<Key>", self._on_key)
        # the canvas must take focus for key events to reach it
        self._widget.bind("<Button-1>", lambda _e: self._widget.focus_set(), add="+")

    # --- public API ----------------------------------------------------------
    def get(self):
        """The current page number."""
        return self._current_page

    def update(
        self,
        current_page: Optional[int] = None,
        total: Any = None,
        page_size: Optional[int] = None,
        visible: Optional[bool] = None):
        """Change the page, the item count or the page size.

        The current page is clamped into the new ``[1, page_count]`` range
        whenever the total or the page size changes.
        """
        redraw = False
        if total is not None:
            if int(total) < 0:
                raise ValueError("total must be zero or greater")
            self._total = int(total)
            redraw = True
        if page_size is not None:
            if int(page_size) < 1:
                raise ValueError("page_size must be at least 1")
            self._page_size = int(page_size)
            redraw = True
        if current_page is not None:
            self._current_page = int(current_page)
            redraw = True
        if redraw:
            self._current_page = self._clamp_page(self._current_page)
            self._hover = None
            self._redraw()
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class TTransfer(Element):
    """Two listboxes with arrows moving items between them.

    The left box holds the source items, the right one the target items --
    what :meth:`get` returns. "›" moves the selected items right, "»" moves
    everything, "‹" and "«" move back; double-clicking an item moves just
    that item. ``size`` is the character size of both listboxes::

        ts.TTransfer(["a", "b", "c"], target_items=["x"], key="-MOVE-")

    Items are plain strings; the arrow buttons are the only chrome, so a
    theme switch just recolors the frame, the titles and the two listboxes.
    """

    __slots__ = (
        "_source",
        "_target",
        "_titles",
        "_enable_events",
        "_font",
        "_source_title",
        "_target_title",
        "_source_list",
        "_target_list",
        "_arrows",
        "_buttons",
    )

    # None until the window is finalized
    _source_title: Optional[tk.Label]
    _target_title: Optional[tk.Label]
    _source_list: Optional[tk.Listbox]
    _target_list: Optional[tk.Listbox]
    _arrows: Optional[tk.Frame]

    def __init__(
        self,
        source_items: Sequence[Any],
        target_items: Optional[Sequence[Any]] = None,
        titles: Sequence[str] = ("Source", "Target"),
        size: Size = (18, 8),
        key: Optional[ElementKey] = None,
        enable_events: bool = False,
        font: Optional[FontSpec] = None,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            size=size if size is not None else (18, 8),
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._source = [str(item) for item in source_items]
        self._target = [str(item) for item in (target_items or ())]
        self._titles = (str(titles[0]), str(titles[1]))
        self._enable_events = bool(enable_events)
        self._font = font
        self._source_title = None
        self._target_title = None
        self._source_list = None
        self._target_list = None
        self._arrows = None
        self._buttons: List[ttk.Button] = []

    @property
    def _bind_target(self):
        """Hover/right-click plumbing follows the source listbox (the frame
        itself never gets the pointer — the children cover it)."""
        return self._source_list if self._source_list is not None else self._widget

    # --- building ------------------------------------------------------------
    def _list_size(self):
        """(width, height) of both listboxes in text units."""
        width = int(self._size[0]) if self._size[0] else 18
        height = int(self._size[1]) if self._size[1] else 8
        return width, height

    def _listbox_options(self, master: tk.Misc):
        """Theme options for the listboxes (sampled defaults when native)."""
        options = theme_mod.theme_manager.input_kwargs(include_caret=False)
        if not options:
            options = theme_mod.native_widget_colors(
                tk.Listbox, master, ("background", "foreground")
            )
        return options

    def _make_listbox(self, master: tk.Misc, width: int, height: int):
        """One listbox, themed and sized in text units."""
        options = self._listbox_options(master)
        if self._font is not None:
            options["font"] = self._font
        return tk.Listbox(
            master,
            selectmode="extended",
            exportselection=False,  # both boxes keep their own selection
            width=width,
            height=height,
            **options
        )

    def _make_arrows(self, master: tk.Misc, colors: _paint.ColorMap):
        """A single row of four move buttons between the two listboxes.

        Order left-to-right: all-target, sel-target, sel-source, all-source.
        Single-row layout matches the keyboard-friendly convention of
        native list-merge controls (vs. the 2×2 grid ported from the web
        twin-listbox, which doubles vertical space with no extra info).
        """
        frame = tk.Frame(master, background=colors["surface"])
        commands = (
            (_DOUBLE_RIGHT, partial(self.move_all, to_target=True)),
            (_CHEVRON_RIGHT, partial(self.move_selected, to_target=True)),
            (_CHEVRON_LEFT, partial(self.move_selected, to_target=False)),
            (_DOUBLE_LEFT, partial(self.move_all, to_target=False)),
        )
        for column, (label, command) in enumerate(commands):
            button = ttk.Button(frame, text=label, width=3, command=command)
            button.grid(row=0, column=column, padx=2, sticky="ew")
            self._buttons.append(button)
        return frame

    def _create_widget(self, master: tk.Misc):
        colors = _paint.palette(master)
        frame = tk.Frame(master, background=colors["surface"])
        width, height = self._list_size()
        self._source_list = self._make_listbox(frame, width, height)
        self._target_list = self._make_listbox(frame, width, height)
        self._arrows = self._make_arrows(frame, colors)
        # column titles are optional: a desktop list with a single-line
        # toolbar of action arrows usually does not need a verbose header
        # row, and the source/target semantic is clear from the arrow
        # direction. Pass titles=("Source", "Target") to restore the
        # header row (still the default for back-compat).
        show_titles = any(self._titles)
        if show_titles:
            self._source_title = self._make_title(frame, self._titles[0], colors)
            self._target_title = self._make_title(frame, self._titles[1], colors)
            self._source_title.grid(row=0, column=0, sticky="w",
                                    padx=(0, 6), pady=(0, 2))
            self._target_title.grid(row=0, column=2, sticky="w",
                                    padx=(6, 0), pady=(0, 2))
        else:
            self._source_title = None
            self._target_title = None
        self._source_list.grid(row=1, column=0, sticky="nsew")
        self._target_list.grid(row=1, column=2, sticky="nsew")
        self._arrows.grid(row=1, column=1, padx=4, sticky="")
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(2, weight=1)
        self._render()
        return frame

    def _make_title(self, master: tk.Misc, text: str, colors: _paint.ColorMap):
        """One muted column title."""
        label = tk.Label(
            master, text=text, anchor="w",
            background=colors["surface"], foreground=colors["muted"],
        )
        if self._font is not None:
            label.configure(font=self._font)
        return label

    def _bind_events(self):
        if self._source_list is not None:
            self._source_list.bind("<Double-Button-1>", partial(self._on_double_click, True))
        if self._target_list is not None:
            self._target_list.bind("<Double-Button-1>", partial(self._on_double_click, False))

    # --- moves ---------------------------------------------------------------
    def _render(self):
        """Mirror the python-side lists into the two listboxes."""
        source_list, target_list = self._source_list, self._target_list
        if source_list is None or target_list is None:
            return
        for listbox, items in ((source_list, self._source), (target_list, self._target)):
            listbox.delete(0, "end")
            for item in items:
                listbox.insert("end", item)
            listbox.selection_clear(0, "end")

    def _move(self, indices: Sequence[int], to_target: bool) -> bool:
        """Move ``indices`` between the lists; True when something moved."""
        origin = self._source if to_target else self._target
        destination = self._target if to_target else self._source
        wanted = {int(index) for index in indices}
        picked = [origin[index] for index in sorted(wanted) if 0 <= index < len(origin)]
        if not picked:
            return False
        origin[:] = [
            item for index, item in enumerate(origin) if index not in wanted
        ]
        destination.extend(picked)
        self._render()
        if self._enable_events:
            self._post_event()
        return True

    def move_selected(self, to_target: bool = True):
        """Move the selected items; False when nothing was selected."""
        listbox = self._source_list if to_target else self._target_list
        if listbox is None:
            return False
        return self._move(listbox.curselection(), to_target)

    def move_all(self, to_target: bool = True):
        """Move every item; False when the origin list was empty."""
        origin = self._source if to_target else self._target
        return self._move(range(len(origin)), to_target)

    def _on_double_click(self, from_source: bool, event: tk.Event):
        """Move the double-clicked item to the other list."""
        listbox = self._source_list if from_source else self._target_list
        if listbox is None:
            return
        index = int(listbox.nearest(event.y))
        box = listbox.bbox(index)
        if box is None or not box[1] <= event.y <= box[1] + box[3]:
            return  # the click landed below the last item
        self._move([index], from_source)

    # --- public API ----------------------------------------------------------
    def get(self):
        """The items currently in the target (right) list."""
        return list(self._target)

    def update(
        self,
        source_items: Optional[Sequence[Any]] = None,
        target_items: Optional[Sequence[Any]] = None,
        visible: Optional[bool] = None):
        """Replace both sides wholesale (any selection is cleared)."""
        if source_items is not None:
            self._source = [str(item) for item in source_items]
        if target_items is not None:
            self._target = [str(item) for item in target_items]
        if source_items is not None or target_items is not None:
            self._render()
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self

    def apply_theme(self):
        """Recolor the frame, the titles and the two listboxes."""
        source_list, target_list = self._source_list, self._target_list
        if self._widget is None or source_list is None or target_list is None:
            return self
        colors = _paint.palette(self._widget)
        self._widget.configure(background=colors["surface"])
        if self._arrows is not None:
            self._arrows.configure(background=colors["surface"])
        for title in (self._source_title, self._target_title):
            if title is not None:
                title.configure(
                    background=colors["surface"], foreground=colors["muted"]
                )
        options = self._listbox_options(source_list)
        for listbox in (source_list, target_list):
            listbox.configure(**options)
        return self
