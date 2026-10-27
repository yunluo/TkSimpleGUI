"""TChart: a high-level plotting element built on the TGraph canvas.

Nine chart types share one declarative data model — line, bar, hbar
(horizontal bars), scatter, area, pie, donut, stacked (stacked bars) and
histogram. Scientific / industrial extras: per-point error bars
(``errors=``), dashed reference lines with labels (``hlines=`` — targets,
spec limits, SPC control limits) and automatic histogram binning
(``bins=``).

Rendering backends, in order of preference:

1. **Pillow** (optional): the data marks are drawn into a 3x supersampled
   image and downscaled with Lanczos, giving properly anti-aliased lines
   and arcs. Install it with ``pip install pillow`` — nothing else in
   TkSimpleGUI requires it.
2. **Tk canvas** (always available): plain vector figures with round line
   joins. Edges are not anti-aliased (Tk's canvas cannot), but rendering
   is instant and every mark stays an individually addressable canvas
   item.

TText, axis lines, tick labels, title and legend are always vector canvas
items, so fonts stay crisp and colors follow the active TkSimpleGUI theme
in both backends. Pass ``anti_alias=False`` to skip the Pillow backend and
always draw vector figures::

    chart = ts.TChart((420, 260), chart_type=ts.ChartType.LINE,
                      title="Revenue", legend=True)
    chart.add_series("2024", [12, 34, 28, 41])
    chart.add_series("2025", [22, 30, 38, 35], labels=["Q1", "Q2", "Q3", "Q4"])
    chart.redraw()

``update_data()`` replaces the values and redraws in one call; pie and
donut charts use ``add_series(label, [(name, value), ...])``. With
``smooth=True`` line/area series are drawn as Catmull-Rom splines through
the data points; ``markers=False`` hides the line-chart point dots.
"""

import math
from typing import List, Optional, Tuple

import tkinter as tk

from .media import TGraph
from ._paint import pil_modules as _paint_pil_modules
from .. import _theming as theme_mod

# --- default palette (cycled per series / per pie slice) ----------------------
PALETTE = (
    "#3a7bd5", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6",
    "#1abc9c", "#e67e22", "#34495e", "#e91e63", "#00bcd4",
)

AXIS_COLOR = "#666666"
GRID_COLOR = "#dddddd"
TEXT_COLOR = "#333333"

PIE_START = 0.0  # degrees; pie drawing runs counter-clockwise from east
DONUT_INNER_RATIO = 0.58
AREA_ALPHA = 110  # 0-255 translucency of the area fill
LINE_WIDTH = 2.0
MARKER_RADIUS = 3.0
SCATTER_RADIUS = 4.0
AA_SCALE = 3  # supersampling factor of the Pillow backend

def _pil_modules():
    """(Image, ImageDraw) when Pillow is installed, else False (cached).

    The probe itself lives in ``_paint`` so the chart backend, the circular
    avatar crop and the rotated watermark share one cache.
    """
    return _paint_pil_modules()


def pil_backend_available():
    """True when the optional Pillow rendering backend can be used."""
    return bool(_pil_modules())


def _hex_rgb(color):
    """``#rrggbb`` (or ``#rgb``) -> ``(r, g, b)``; invalid names fall back."""
    text = (color or "#000000").lstrip("#")
    if len(text) == 3:
        text = "".join(ch * 2 for ch in text)
    if len(text) != 6:
        return (0, 0, 0)
    try:
        return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return (0, 0, 0)


def _resample_lanczos(image_mod):
    """The Lanczos resampling filter across Pillow versions."""
    try:
        return image_mod.Resampling.LANCZOS
    except AttributeError:  # Pillow < 9.1
        return image_mod.LANCZOS


class ChartType:
    """TChart kind names accepted by ``TChart(chart_type=...)``."""

    LINE = "line"
    BAR = "bar"
    HBAR = "hbar"
    SCATTER = "scatter"
    AREA = "area"
    PIE = "pie"
    DONUT = "donut"
    STACKED = "stacked"
    HISTOGRAM = "histogram"

    ALL = (LINE, BAR, HBAR, SCATTER, AREA, PIE, DONUT, STACKED, HISTOGRAM)


LEGEND_POSITIONS = ("top", "bottom", "left", "right")


class _Series:
    """One data series (or, for pie/donut charts, the labelled slice set)."""

    __slots__ = ("name", "values", "labels", "color", "errors")

    def __init__(self, name, values, labels=None, color=None, errors=None):
        self.name = name
        self.values = list(values)
        self.labels = list(labels) if labels is not None else []
        self.color = color
        self.errors = list(errors) if errors is not None else []

    @property
    def total(self):
        return float(sum(value for _name, value in self.pairs))

    @property
    def pairs(self):
        """(label, value) pairs; labels default to the 1-based index."""
        out = []
        for index, value in enumerate(self.values):
            label = self.labels[index] if index < len(self.labels) else str(index + 1)
            out.append((label, value))
        return out


def _spline_path(points, steps=12):
    """Catmull-Rom spline through ``points`` (sampled densely)."""
    if len(points) < 3:
        return list(points)
    extended = [points[0], *points, points[-1]]
    out = []
    for i in range(len(extended) - 3):
        p0, p1, p2, p3 = extended[i:i + 4]
        for step in range(steps):
            t = step / steps
            t2, t3 = t * t, t * t * t
            out.append((
                0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
                       + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                       + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3),
            ))
    out.append(points[-1])
    return out


def _normalize_hlines(entries):
    """Normalize the ``hlines`` argument to ``[(value, label, color), ...]``.

    Accepts a single entry or a list; each entry is a number, a
    ``(value, label)`` tuple or a ``(value, label, color)`` tuple.
    """
    if entries is None:
        return []
    if isinstance(entries, (int, float)):
        entries = [entries]
    out = []
    for entry in entries:
        if isinstance(entry, (int, float)):
            out.append((float(entry), None, None))
        elif len(entry) == 2:
            value, label = entry
            out.append((float(value), str(label), None))
        else:
            value, label, color = entry
            out.append((float(value), str(label), color))
    return out


class TChart(TGraph):
    """A multi-type plotting element on the TGraph user coordinate system.

    Args:
        canvas_size: pixel size of the underlying canvas.
        chart_type: one of :class:`ChartType` ("line" default).
        title: chart title drawn at the top (None hides it).
        legend: show a legend (line/bar/hbar/scatter/area/stacked, pie/donut).
        legend_position: "top" / "bottom" / "left" / "right" (Excel style;
            the plot area shrinks to make room for horizontal legends).
        grid: draw horizontal+vertical grid lines behind the data.
        axis_labels: ``(x_title, y_title)`` axis captions.
        colors: palette used to cycle series/slice colors.
        anti_alias: use the optional Pillow backend for smooth data marks
            (default True; silently falls back to Tk canvas figures when
            Pillow is not installed).
        smooth: draw line/area series as splines through the data points.
        markers: show the point dots on line charts (and spline charts).
        hlines: dashed horizontal reference lines — one entry or a list of
            ``value`` / ``(value, label)`` / ``(value, label, color)``
            tuples. Targets, specification limits, SPC control limits.
        bins: histogram bin count (default: Freedman-Diaconis-ish auto).
    """

    __slots__ = (
        "_chart_type", "_title", "_legend", "_legend_position", "_grid",
        "_axis_labels", "_palette", "_series", "_auto_range", "_x_range",
        "_y_range", "_pie_labels", "_anti_alias", "_smooth", "_markers",
        "_hlines", "_bins",
    )

    def __init__(
        self,
        canvas_size=(420, 280),
        chart_type="line",
        title=None,
        legend=True,
        legend_position="right",
        grid=True,
        axis_labels=None,
        colors=PALETTE,
        anti_alias=True,
        smooth=False,
        markers=True,
        hlines=None,
        bins=None,
        graph_bottom_left=(0, 0),
        graph_top_right=(100, 100),
        background_color=None,
        key=None,
        enable_events=False,
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        right_click_menu=None,
        metadata=None,
    ):
        if chart_type not in ChartType.ALL:
            raise ValueError(
                f"chart_type must be one of {ChartType.ALL}, got {chart_type!r}"
            )
        if legend_position not in LEGEND_POSITIONS:
            raise ValueError(
                f"legend_position must be one of {LEGEND_POSITIONS}, "
                f"got {legend_position!r}"
            )
        super().__init__(
            canvas_size=canvas_size,
            graph_bottom_left=graph_bottom_left,
            graph_top_right=graph_top_right,
            background_color=background_color,
            key=key,
            enable_events=enable_events,
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._chart_type = chart_type
        self._title = title
        self._legend = bool(legend)
        self._legend_position = legend_position
        self._grid = bool(grid)
        self._axis_labels = axis_labels
        self._palette = list(colors)
        self._series: List[_Series] = []
        self._auto_range = (
            graph_bottom_left == (0, 0) and graph_top_right == (100, 100)
        )
        self._x_range: Optional[Tuple[float, float]] = None
        self._y_range: Optional[Tuple[float, float]] = None
        self._pie_labels: List[Tuple[str, str]] = []
        self._anti_alias = bool(anti_alias)
        self._smooth = bool(smooth)
        self._markers = bool(markers)
        self._hlines = _normalize_hlines(hlines)
        self._bins = max(1, int(bins)) if bins is not None else None

    # --- data model -------------------------------------------------------------
    def add_series(self, name, values, labels=None, color=None, errors=None):
        """Append one series (``[(name, value), ...]`` for pie/donut).

        ``errors`` adds symmetric error bars (one magnitude per point) on
        line/scatter/bar/area/stacked charts.
        """
        if self._chart_type in (ChartType.PIE, ChartType.DONUT):
            pairs = [(str(label), float(value)) for label, value in values]
            self._series = [
                _Series(
                    name,
                    [value for _label, value in pairs],
                    [label for label, _value in pairs],
                    color,
                )
            ]
        else:
            series = _Series(name, values, labels, color, errors)
            if series.errors and len(series.errors) != len(series.values):
                raise ValueError(
                    "errors must have the same length as values "
                    f"(got {len(series.errors)} errors for {len(series.values)} values)"
                )
            self._series.append(series)
        return self

    def clear_series(self):
        """Remove every series (chart stays configured)."""
        self._series = []
        return self

    def update_data(self, series_name, values, labels=None, errors=None):
        """Replace one series' values and redraw (pie/donut: values = pairs)."""
        for series in self._series:
            if series.name == series_name:
                if self._chart_type in (ChartType.PIE, ChartType.DONUT):
                    pairs = [(str(label), float(value)) for label, value in values]
                    series.values = [value for _label, value in pairs]
                    series.labels = [label for label, _value in pairs]
                else:
                    series.values = list(values)
                    if labels is not None:
                        series.labels = list(labels)
                    if errors is not None:
                        if len(errors) != len(series.values):
                            raise ValueError(
                                "errors must have the same length as values"
                            )
                        series.errors = list(errors)
                break
        else:
            raise KeyError(f"no series named {series_name!r}")
        return self.redraw()

    @property
    def series_names(self):
        return [series.name for series in self._series]

    # --- theme-aware colors -------------------------------------------------------
    def _surface_color(self):
        """The chart surface as #rrggbb (theme aware, native fallback)."""
        color = self._background_color
        if color is None:
            color = theme_mod.theme_manager.effective_background()
        if color is None:
            color = str(self._widget.cget("background"))
        red, green, blue = self._widget.winfo_rgb(color)
        return f"#{red >> 8:02x}{green >> 8:02x}{blue >> 8:02x}"

    def _ink_color(self):
        """Label/text color: theme text when themed, classic gray otherwise."""
        color = theme_mod.theme_manager.text_color
        if color is None or theme_mod._is_system_default(color):
            return TEXT_COLOR
        red, green, blue = self._widget.winfo_rgb(color)
        return f"#{red >> 8:02x}{green >> 8:02x}{blue >> 8:02x}"

    def _blend(self, other, ratio):
        """Blend the surface toward ``other`` by ``ratio`` (0..1)."""
        sr, sg, sb = _hex_rgb(self._surface_color())
        orr, og, ob = _hex_rgb(other)
        mixed = (
            round(sr + (orr - sr) * ratio),
            round(sg + (og - sg) * ratio),
            round(sb + (ob - sb) * ratio),
        )
        return "#{:02x}{:02x}{:02x}".format(*mixed)

    def _grid_color(self):
        return self._blend(self._ink_color(), 0.12)

    def _axis_color(self):
        return self._blend(self._ink_color(), 0.45)

    def _panel_color(self):
        return self._blend(self._ink_color(), 0.05)

    def _color(self, index):
        return self._palette[index % len(self._palette)]

    # --- coordinate framing -------------------------------------------------------
    def _data_bounds(self):
        """(x_min, x_max, y_min, y_max) over all series (None for pie/donut)."""
        if self._chart_type in (ChartType.PIE, ChartType.DONUT):
            return None
        if not self._series:
            return None
        if self._chart_type == ChartType.HISTOGRAM:
            edges, counts = self._histogram_bins()
            y_max = max([1.0, *counts])
            return (edges[0], edges[-1], 0.0, y_max * 1.08)
        count = max(len(series.values) for series in self._series)
        if self._chart_type == ChartType.STACKED:
            values = [
                sum(s.values[i] for s in self._series if i < len(s.values))
                for i in range(count)
            ]
        else:
            values = [value for series in self._series for value in series.values]
            # error bars must fit: extend the range by each error magnitude
            for series in self._series:
                for index, value in enumerate(series.values):
                    if index < len(series.errors):
                        magnitude = series.errors[index]
                        values.append(value + magnitude)
                        values.append(value - magnitude)
        if self._chart_type == ChartType.HBAR:
            # hbar swaps axes: values scale along x, categories along y
            # (hlines are y-axis references and do not apply here)
            x_min = min([0.0, *values])
            x_max = max([1.0, *values])
            x_pad = (x_max - x_min) * 0.08
            return (x_min, x_max + x_pad, 0.0, float(count))
        values.extend(value for value, _label, _color in self._hlines)
        y_min = min([0.0, *values]) if values else 0.0
        y_max = max(values) if values else 1.0
        if y_max == y_min:
            y_max = y_min + 1.0
        pad = (y_max - y_min) * 0.08
        x_max = (max(count - 1, 1) if self._chart_type in
                 (ChartType.LINE, ChartType.SCATTER) else count)
        return (0, x_max, y_min - pad, y_max + pad)

    def _histogram_bins(self):
        """(edges, counts) — one shared binning over every series' values."""
        values = [value for series in self._series for value in series.values]
        if not values:
            edges = [0.0, 1.0]
            return edges, [0]
        low, high = min(values), max(values)
        if high == low:
            high = low + 1.0
        bins = self._bins
        if bins is None:
            # Freedman-Diaconis-ish: sqrt fallback keeps it dependency-free
            bins = max(1, int(math.ceil(math.sqrt(len(values)))))
        width = (high - low) / bins
        counts = [0] * bins
        for value in values:
            index = min(bins - 1, int((value - low) / width))
            counts[index] += 1
        edges = [low + width * i for i in range(bins + 1)]
        return edges, counts

    def _apply_auto_range(self):
        if not self._auto_range:
            return
        bounds = self._data_bounds()
        if bounds is None:
            return
        x_min, x_max, y_min, y_max = bounds
        self._bottom_left = (x_min, y_min)
        self._top_right = (x_max, y_max)
        self._x_range = (x_min, x_max)
        self._y_range = (y_min, y_max)
        self._compute_scale()

    # --- drawing ------------------------------------------------------------------
    def _post_create(self):
        super()._post_create()
        # first render right after the canvas exists: layouts are usually
        # declared before the window finalizes, so an explicit redraw()
        # call at declaration time would silently do nothing
        self.redraw()

    def redraw(self):
        """Recompute framing and render everything from the current data."""
        if self._widget is None:
            return self
        self.widget.delete("all")
        self._images = []  # drop the previous raster frame
        self._pie_labels = []
        surface = self._surface_color()
        self._widget.configure(background=surface)
        round_kind = self._chart_type in (ChartType.PIE, ChartType.DONUT)
        if round_kind:
            primitives = self._pie_primitives(surface)
        else:
            self._apply_auto_range()
            # the Pillow frame is an opaque full-canvas photo, so the grid
            # is drawn INTO it; the vector fallback renders the same prims
            primitives = self._grid_primitives() + self._data_primitives()
        if not (self._anti_alias and self._draw_primitives_pil(primitives, surface)):
            self._draw_primitives_vector(primitives)
        if not round_kind:
            # reference lines sit above the data but below axes/labels
            self._draw_hlines()
        if round_kind:
            self._draw_round_legend()
        else:
            self._draw_axes()
        self._draw_title()
        if self._legend and not round_kind:
            self._draw_legend()
        return self

    def apply_theme(self):
        """Repaint surface and data layer with the active palette."""
        self.redraw()
        return self

    # coordinate helpers operating in PIXELS on the underlying canvas
    def _plot_rect(self):
        """Pixel rect (left, top, right, bottom) the plot area occupies."""
        width = float(self._canvas_size[0])
        height = float(self._canvas_size[1])
        left = 46.0
        right = width - 12.0
        top = 30.0
        bottom = height - 34.0
        if self._axis_labels and self._axis_labels[1]:
            left += 12.0
        # reserve bands for a horizontal legend, Excel style
        if self._legend and self._legend_position == "top":
            top = 48.0
        if self._legend and self._legend_position == "bottom":
            bottom = height - 56.0
        if self._legend and self._legend_position == "left":
            left = max(left, 116.0)
        return (left, top, right, bottom)

    def _px(self, value, axis):
        """Map a data value on ``axis`` ("x"/"y") to a pixel coordinate."""
        left, top, right, bottom = self._plot_rect()
        if axis == "x":
            x_min, x_max = self._x_range or (0, 100)
            if x_max == x_min:
                x_max = x_min + 1
            return left + (value - x_min) / (x_max - x_min) * (right - left)
        y_min, y_max = self._y_range or (0, 100)
        if y_max == y_min:
            y_max = y_min + 1
        return bottom - (value - y_min) / (y_max - y_min) * (bottom - top)

    def _nice_ticks(self, lo, hi, count=5):
        """Round tick steps to 1/2/5*10^n for readable axis labels."""
        span = (hi - lo) or 1.0
        raw = span / count
        magnitude = 10 ** math.floor(math.log10(raw))
        for multiplier in (1, 2, 5, 10):
            step = magnitude * multiplier
            if step >= raw:
                break
        start = math.ceil(lo / step) * step
        ticks = []
        value = start
        while value <= hi + 1e-9:
            ticks.append(value)
            value += step
        return ticks

    # --- grid / axes (vector: crisp lines and text) ---------------------------------
    def _grid_primitives(self):
        """Grid lines as 1px rectangle primitives (raster or vector)."""
        if not self._grid:
            return []
        left, top, right, bottom = self._plot_rect()
        grid = self._grid_color()
        prims = []
        for tick in self._nice_ticks(*self._y_range or (0, 100)):
            y = self._px(tick, "y")
            prims.append(("rectangle", (left, y - 0.5, right, y + 0.5), grid))
        for tick in self._nice_ticks(*self._x_range or (0, 100)):
            x = self._px(tick, "x")
            prims.append(("rectangle", (x - 0.5, top, x + 0.5, bottom), grid))
        return prims

    def _draw_axes(self):
        left, top, right, bottom = self._plot_rect()
        widget = self._widget
        axis = self._axis_color()
        ink = self._ink_color()
        widget.create_line(left, top, left, bottom, fill=axis, width=1)
        widget.create_line(left, bottom, right, bottom, fill=axis, width=1)
        # tick labels (hbar's y axis is categorical: names come from labels)
        if self._chart_type != ChartType.HBAR:
            for tick in self._nice_ticks(*self._y_range or (0, 100)):
                y = self._px(tick, "y")
                widget.create_text(
                    left - 6, y, text=self._fmt(tick), anchor="e",
                    fill=ink, font=("TkDefaultFont", 8),
                )
        count = max((len(s.values) for s in self._series), default=0)
        if self._chart_type == ChartType.HISTOGRAM:
            # histogram x axis is a numeric axis: real value ticks, Excel style
            for tick in self._nice_ticks(*self._x_range or (0, 100)):
                x = self._px(tick, "x")
                widget.create_text(
                    x, bottom + 10, text=self._fmt(tick), anchor="n",
                    fill=ink, font=("TkDefaultFont", 8),
                )
        elif count:
            labels = self._series[0].labels or [
                str(i + 1) for i in range(count)
            ]
            if self._chart_type == ChartType.HBAR:
                # category names sit at the left of each horizontal bar
                slot = (bottom - top) / max(count, 1)
                for i in range(count):
                    y = top + slot * (i + 0.5)
                    widget.create_text(
                        left - 6, y, text=labels[i], anchor="e",
                        fill=ink, font=("TkDefaultFont", 8),
                    )
            else:
                category = self._chart_type in (ChartType.BAR, ChartType.STACKED)
                step = (right - left) / max(count, 1)
                for i in range(count):
                    x = left + step * (i + 0.5) if category else self._px(i, "x")
                    widget.create_text(
                        x, bottom + 10, text=labels[i], anchor="n",
                        fill=ink, font=("TkDefaultFont", 8),
                    )
        if self._axis_labels:
            x_title, y_title = self._axis_labels
            if x_title:
                widget.create_text(
                    (left + right) / 2, bottom + 24, text=x_title,
                    anchor="n", fill=ink, font=("TkDefaultFont", 8),
                )
            if y_title:
                widget.create_text(
                    12, (top + bottom) / 2, text=y_title, angle=90,
                    anchor="w", fill=ink, font=("TkDefaultFont", 8),
                )

    @staticmethod
    def _fmt(value):
        if float(value).is_integer():
            return str(int(value))
        return f"{value:.2f}".rstrip("0").rstrip(".")

    def _hline_color(self, explicit):
        """Reference-line color: explicit, else a calm industrial red."""
        if explicit:
            return explicit
        # blend toward the alarm hue so it reads on both light/dark themes
        return self._blend("#c62828", 0.85)

    def _draw_hlines(self):
        """Dashed reference lines with right-aligned labels (vector layer)."""
        if not self._hlines or self._chart_type == ChartType.HBAR:
            return
        left, top, right, bottom = self._plot_rect()
        widget = self._widget
        for value, label, color in self._hlines:
            y = self._px(value, "y")
            if y < top - 1 or y > bottom + 1:
                continue  # outside the plot: skip rather than clip ugly
            line_color = self._hline_color(color)
            widget.create_line(
                left, y, right, y, fill=line_color,
                width=1, dash=(5, 3),
            )
            if label:
                widget.create_text(
                    right - 4, y - 9, text=label, anchor="e",
                    fill=line_color, font=("TkDefaultFont", 8),
                )

    # --- data layer: one primitive list, two renderers ------------------------------
    def _data_primitives(self):
        """The data marks as renderer-neutral primitive tuples."""
        if self._chart_type == ChartType.STACKED:
            return self._stacked_primitives()
        if self._chart_type == ChartType.HISTOGRAM:
            return self._histogram_primitives()
        handlers = {
            ChartType.LINE: self._line_primitives,
            ChartType.SCATTER: self._scatter_primitives,
            ChartType.AREA: self._area_primitives,
        }
        prims = []
        for index, series in enumerate(self._series):
            color = series.color or self._color(index)
            if self._chart_type in handlers:
                prims.extend(handlers[self._chart_type](series, color))
            elif self._chart_type == ChartType.BAR:
                prims.extend(self._bar_primitives(series, index))
            elif self._chart_type == ChartType.HBAR:
                prims.extend(self._hbar_primitives(series, index))
        return prims

    def _histogram_primitives(self):
        """Histogram bars — all series' values share one binning grid."""
        if not self._series:
            return []
        edges, counts = self._histogram_bins()
        _left, _top, _right, bottom = self._plot_rect()
        color = self._series[0].color or self._color(0)
        prims = []
        for index, count in enumerate(counts):
            if count <= 0:
                continue
            x0 = self._px(edges[index], "x")
            x1 = self._px(edges[index + 1], "x")
            y = self._px(count, "y")
            prims.append(("rectangle", (x0, y, x1, bottom), color))
        return prims

    def _error_bar_primitives(self, anchors, series, color, cap=3.0):
        """Symmetric error bars: main line + two caps, as line primitives.

        ``anchors`` is a list of ``(pixel_x, data_value)`` pairs — the
        marker / bar-center positions the error bars ride on.
        """
        prims = []
        for index, (x, value) in enumerate(anchors):
            if index >= len(series.errors):
                break
            magnitude = series.errors[index]
            y_high = self._px(value + magnitude, "y")
            y_low = self._px(value - magnitude, "y")
            prims.append(("line", [(x, y_low), (x, y_high)], color, 1.2))
            prims.append(("line", [(x - cap, y_high), (x + cap, y_high)], color, 1.2))
            prims.append(("line", [(x - cap, y_low), (x + cap, y_low)], color, 1.2))
        return prims

    def _hbar_error_bar_primitives(self, series, color, cap=3.0):
        """Horizontal error bars for hbar charts (error spans the x axis)."""
        _left, top, _right, bottom = self._plot_rect()
        count = max(len(s.values) for s in self._series)
        slot = (bottom - top) / max(count, 1)
        group_count = len(self._series)
        bar_height = slot * 0.7 / group_count
        series_index = self._series.index(series)
        prims = []
        for index, value in enumerate(series.values):
            if index >= len(series.errors):
                break
            magnitude = series.errors[index]
            y_center = top + slot * (index + 0.5)
            offset = (series_index - (group_count - 1) / 2.0) * bar_height
            y = y_center + offset
            x_high = self._px(value + magnitude, "x")
            x_low = self._px(value - magnitude, "x")
            prims.append(("line", [(x_low, y), (x_high, y)], color, 1.2))
            prims.append(("line", [(x_low, y - cap), (x_low, y + cap)], color, 1.2))
            prims.append(("line", [(x_high, y - cap), (x_high, y + cap)], color, 1.2))
        return prims

    def _stacked_primitives(self):
        """Stacked bars: one pass over series so segments share running totals."""
        if not self._series:
            return []
        left, _top, right, bottom = self._plot_rect()
        count = max(len(s.values) for s in self._series)
        slot = (right - left) / max(count, 1)
        bar_width = slot * 0.7
        prims = []
        running = [0.0] * count
        for index, series in enumerate(self._series):
            color = self._color(index)
            for i, value in enumerate(series.values):
                x_center = left + slot * (i + 0.5)
                y_top = self._px(running[i] + value, "y")
                y_base = self._px(running[i], "y")
                prims.append(("rectangle", (
                    x_center - bar_width / 2, y_top,
                    x_center + bar_width / 2, y_base,
                ), color))
                running[i] += value
        return prims

    def _line_primitives(self, series, color):
        points = [
            (self._px(i, "x"), self._px(v, "y"))
            for i, v in enumerate(series.values)
        ]
        path = _spline_path(points) if self._smooth else points
        prims = [("line", path, color, LINE_WIDTH)]
        if series.errors:
            anchors = [
                (self._px(i, "x"), value)
                for i, value in enumerate(series.values)
            ]
            prims.extend(self._error_bar_primitives(anchors, series, color))
        if self._markers:
            for x, y in points:
                prims.append((
                    "ellipse",
                    (x - MARKER_RADIUS, y - MARKER_RADIUS,
                     x + MARKER_RADIUS, y + MARKER_RADIUS),
                    color, color,
                ))
        return prims

    def _scatter_primitives(self, series, color):
        prims = []
        if series.errors:
            anchors = [
                (self._px(i, "x"), value)
                for i, value in enumerate(series.values)
            ]
            prims.extend(self._error_bar_primitives(anchors, series, color))
        prims.extend(
            ("ellipse",
             (self._px(i, "x") - SCATTER_RADIUS, self._px(v, "y") - SCATTER_RADIUS,
              self._px(i, "x") + SCATTER_RADIUS, self._px(v, "y") + SCATTER_RADIUS),
             color, "")
            for i, v in enumerate(series.values)
        )
        return prims

    def _area_primitives(self, series, color):
        left, top, right, bottom = self._plot_rect()
        baseline = bottom
        points = [(left, baseline)]
        points.extend(
            (self._px(i, "x"), self._px(v, "y"))
            for i, v in enumerate(series.values)
        )
        points.append((self._px(len(series.values) - 1, "x"), baseline))
        prims = [("polygon", points, color, True)]  # True = translucent
        prims.extend(self._line_primitives(series, color))
        return prims

    def _bar_primitives(self, series, series_index):
        left, _top, right, bottom = self._plot_rect()
        count = max(len(s.values) for s in self._series)
        slot = (right - left) / max(count, 1)
        group_count = len(self._series)
        bar_width = slot * 0.7 / group_count
        color = self._color(series_index)
        prims = []
        for i, value in enumerate(series.values):
            x_center = left + slot * (i + 0.5)
            offset = (series_index - (group_count - 1) / 2.0) * bar_width
            x0 = x_center + offset - bar_width / 2
            x1 = x_center + offset + bar_width / 2
            y = self._px(value, "y")
            prims.append(("rectangle", (x0, y, x1, bottom), color))
        if series.errors:
            # error bar rides the bar's center line, from the top upward
            centers = [
                (left + slot * (i + 0.5)
                 + (series_index - (group_count - 1) / 2.0) * bar_width, value)
                for i, value in enumerate(series.values)
            ]
            prims.extend(self._error_bar_primitives(centers, series, color))
        return prims

    def _hbar_primitives(self, series, series_index):
        left, top, right, bottom = self._plot_rect()
        count = max(len(s.values) for s in self._series)
        slot = (bottom - top) / max(count, 1)
        group_count = len(self._series)
        bar_height = slot * 0.7 / group_count
        x_range = self._x_range or (0, 100)
        x_max = x_range[1] or 1.0
        color = self._color(series_index)
        prims = []
        for i, value in enumerate(series.values):
            y_center = top + slot * (i + 0.5)
            offset = (series_index - (group_count - 1) / 2.0) * bar_height
            y0 = y_center + offset - bar_height / 2
            y1 = y_center + offset + bar_height / 2
            length = (
                (value - x_range[0]) / (x_max or 1.0) * (right - left)
            )
            prims.append(("rectangle", (left, y0, left + length, y1), color))
        if series.errors:
            prims.extend(self._hbar_error_bar_primitives(series, color))
        return prims

    def _pie_primitives(self, surface):
        series = self._series[0] if self._series else None
        prims = []
        if series is None or not series.values:
            return prims
        cx, cy, radius = self._pie_center_radius()
        total = series.total or 1.0
        donut = self._chart_type == ChartType.DONUT
        angle = PIE_START
        for i, (label, value) in enumerate(series.pairs):
            extent = value / total * 360.0
            color = series.color or self._color(i)
            prims.append(("wedge", (cx, cy, radius, angle, extent), color))
            self._pie_labels.append((label, color))
            angle += extent
        # soft separators between slices, in surface color
        angle = PIE_START
        for _label, value in series.pairs:
            angle += value / total * 360.0
            radians = math.radians(angle)
            prims.append((
                "line",
                [(cx, cy), (cx + math.cos(radians) * radius,
                            cy - math.sin(radians) * radius)],
                surface, 1.2,
            ))
        if donut:
            inner = radius * DONUT_INNER_RATIO
            prims.append(("circle", (cx, cy, inner), surface))
        return prims

    def _draw_primitives_vector(self, primitives):
        widget = self._widget
        for prim in primitives:
            kind = prim[0]
            if kind == "line":
                _tag, points, color, width = prim
                flat = [coordinate for point in points for coordinate in point]
                if len(flat) >= 4:
                    widget.create_line(
                        *flat, fill=color, width=max(1, int(math.ceil(width))),
                        joinstyle="round", capstyle="round",
                    )
            elif kind == "ellipse":
                _tag, bbox, fill, outline = prim
                widget.create_oval(*bbox, fill=fill, outline=outline)
            elif kind == "circle":
                _tag, (cx, cy, radius), fill = prim
                widget.create_oval(
                    cx - radius, cy - radius, cx + radius, cy + radius,
                    fill=fill, outline="",
                )
            elif kind == "rectangle":
                _tag, bbox, fill = prim
                widget.create_rectangle(*bbox, fill=fill, outline="")
            elif kind == "polygon":
                _tag, points, fill, translucent = prim
                flat = [coordinate for point in points for coordinate in point]
                kwargs = {"stipple": "gray50"} if translucent else {}
                widget.create_polygon(*flat, fill=fill, outline="", **kwargs)
            elif kind == "wedge":
                _tag, (cx, cy, radius, angle, extent), color = prim
                start = -(angle + extent) + 90
                widget.create_arc(
                    cx - radius, cy - radius, cx + radius, cy + radius,
                    start=start, extent=max(extent, 0.01),
                    style="pieslice", fill=color, outline="",
                )

    def _draw_primitives_pil(self, primitives, surface):
        """Render the data layer through the optional Pillow backend."""
        modules = _pil_modules()
        if not modules:
            return False
        image_mod, draw_mod = modules
        scale = AA_SCALE
        width = max(1, int(self._canvas_size[0]))
        height = max(1, int(self._canvas_size[1]))
        try:
            image = image_mod.new("RGB", (width * scale, height * scale), surface)
            draw = draw_mod.Draw(image)

            def scaled(points):
                return [(x * scale, y * scale) for x, y in points]

            for prim in primitives:
                kind = prim[0]
                if kind == "line":
                    _tag, points, color, stroke_width = prim
                    path = scaled(points)
                    line_width = max(1, int(round(stroke_width * scale)))
                    draw.line(path, fill=color, width=line_width, joint="curve")
                    radius = line_width / 2.0  # round caps
                    for x, y in (path[0], path[-1]):
                        draw.ellipse(
                            (x - radius, y - radius, x + radius, y + radius),
                            fill=color,
                        )
                elif kind == "ellipse":
                    _tag, (x0, y0, x1, y1), fill, _outline = prim
                    draw.ellipse(
                        [x0 * scale, y0 * scale, x1 * scale, y1 * scale],
                        fill=fill,
                    )
                elif kind == "circle":
                    _tag, (cx, cy, radius), fill = prim
                    draw.ellipse(
                        [(cx - radius) * scale, (cy - radius) * scale,
                         (cx + radius) * scale, (cy + radius) * scale],
                        fill=fill,
                    )
                elif kind == "rectangle":
                    _tag, (x0, y0, x1, y1), fill = prim
                    draw.rectangle(
                        [x0 * scale, y0 * scale, x1 * scale, y1 * scale],
                        fill=fill,
                    )
                elif kind == "polygon":
                    _tag, points, fill, translucent = prim
                    if translucent:
                        overlay = image_mod.new("RGBA", image.size, (0, 0, 0, 0))
                        draw_mod.Draw(overlay).polygon(
                            scaled(points),
                            fill=(*_hex_rgb(fill), AREA_ALPHA),
                        )
                        image = image_mod.alpha_composite(
                            image.convert("RGBA"), overlay
                        ).convert("RGB")
                        draw = draw_mod.Draw(image)
                    else:
                        draw.polygon(scaled(points), fill=fill)
                elif kind == "wedge":
                    _tag, (cx, cy, radius, angle, extent), color = prim
                    bbox = [
                        (cx - radius) * scale, (cy - radius) * scale,
                        (cx + radius) * scale, (cy + radius) * scale,
                    ]
                    # PIL measures clockwise from 3 o'clock; our wedges run
                    # counter-clockwise, so mirror the sweep
                    draw.pieslice(
                        bbox, -(angle + extent), -angle,
                        fill=color,
                    )
            image = image.resize(
                (width, height), _resample_lanczos(image_mod)
            )
            header = f"P6\n{width} {height}\n255\n".encode("ascii")
            photo = tk.PhotoImage(
                data=header + image.tobytes(), master=self._widget
            )
        except Exception:
            return False
        self._images.append(photo)
        self._widget.create_image(0, 0, anchor="nw", image=photo)
        return True

    # --- legends / titles -------------------------------------------------------------
    def _pie_center_radius(self):
        """Pie/donut geometry, nudged away from the legend band."""
        width = float(self._canvas_size[0])
        height = float(self._canvas_size[1])
        position = self._legend_position if self._legend else None
        cx = width * (0.62 if position == "left" else 0.38)
        cy = height * (0.45 if position == "bottom" else 0.55)
        radius = min(width * 0.34,
                     height * (0.30 if position == "bottom" else 0.38))
        return cx, cy, radius

    @staticmethod
    def _legend_item_width(name):
        """Pixel width of one horizontal legend entry."""
        return 14 + 6 + len(name) * 7 + 14

    def _draw_legend_row(self, x, y, items):
        """One horizontal legend row anchored at (x, y)."""
        ink = self._ink_color()
        for color, name in items:
            self._widget.create_rectangle(
                x, y - 4, x + 14, y + 6, fill=color, outline="",
            )
            self._widget.create_text(
                x + 20, y, text=name, anchor="w",
                fill=ink, font=("TkDefaultFont", 8),
            )
            x += self._legend_item_width(name)

    def _legend_row_y(self):
        """Vertical anchor for a top legend row (below the title if any)."""
        return 34.0 if self._title else 24.0

    def _draw_round_legend(self):
        if not (self._legend and self._pie_labels):
            return
        width = float(self._canvas_size[0])
        height = float(self._canvas_size[1])
        _cx, cy, radius = self._pie_center_radius()
        items = list(self._pie_labels)
        if self._legend_position in ("top", "bottom"):
            total = sum(self._legend_item_width(name) for _c, name in items)
            y = (self._legend_row_y() if self._legend_position == "top"
                 else height - 14.0)
            self._draw_legend_row((width - total) / 2.0, y, items)
            return
        legend_x = width * 0.72 if self._legend_position == "right" else 10.0
        legend_y = cy - radius * 0.7
        ink = self._ink_color()
        for i, (label, color) in enumerate(items):
            y = legend_y + i * 18
            self._widget.create_rectangle(
                legend_x, y - 4, legend_x + 10, y + 6,
                fill=color, outline="",
            )
            self._widget.create_text(
                legend_x + 16, y, text=label, anchor="w",
                fill=ink, font=("TkDefaultFont", 8),
            )

    def _draw_title(self):
        if not self._title:
            return
        width = float(self._canvas_size[0])
        self._widget.create_text(
            width / 2, 12, text=self._title, anchor="n",
            fill=self._ink_color(), font=("TkDefaultFont", 10, "bold"),
        )

    def _draw_legend(self):
        if not self._series:
            return
        items = [
            (series.color or self._color(i), series.name)
            for i, series in enumerate(self._series)
        ]
        width = float(self._canvas_size[0])
        if self._legend_position in ("top", "bottom"):
            total = sum(self._legend_item_width(name) for _c, name in items)
            _left, _top, _right, bottom = self._plot_rect()
            y = self._legend_row_y() if self._legend_position == "top" \
                else bottom + 30.0
            self._draw_legend_row((width - total) / 2.0, y, items)
            return
        # vertical floating box, right or left of the plot
        text_width = max(len(name) for _color, name in items)
        box_w = 14 + text_width * 7 + 18
        box_h = 10 + 16 * len(items)
        x1 = (width - box_w - 8) if self._legend_position == "right" else 8.0
        y0 = 22
        self._widget.create_rectangle(
            x1, y0, x1 + box_w, y0 + box_h,
            fill=self._panel_color(), outline=self._grid_color(),
        )
        ink = self._ink_color()
        y = y0 + 10
        for color, name in items:
            self._widget.create_rectangle(
                x1 + 6, y - 4, x1 + 20, y + 6,
                fill=color, outline="",
            )
            self._widget.create_text(
                x1 + 26, y, text=name, anchor="w",
                fill=ink, font=("TkDefaultFont", 8),
            )
            y += 16
