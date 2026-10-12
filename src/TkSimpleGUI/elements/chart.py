"""Chart: a high-level plotting element built on the Graph canvas.

Six chart types share one declarative data model — line, bar, hbar
(horizontal bars), scatter, area and pie. Charts are plain Tk canvas
figures (no images, no third-party deps), so they rescale with the
graph coordinate system, and every drawn figure id is recorded per
series for post-hoc styling through ``chart.widget.itemconfigure``::

    chart = sg.TChart((420, 260), chart_type=sg.ChartType.LINE,
                      title="Revenue", legend=True)
    chart.add_series("2024", [12, 34, 28, 41])
    chart.add_series("2025", [22, 30, 38, 35], labels=["Q1", "Q2", "Q3", "Q4"])
    chart.redraw()

``update_data()`` replaces the values and redraws in one call; pie charts
use ``add_series(label, [(name, value), ...])``.
"""

import math
from typing import List, Optional, Tuple

from .media import Graph

# --- default palette (cycled per series / per pie slice) ----------------------
PALETTE = (
    "#3a7bd5", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6",
    "#1abc9c", "#e67e22", "#34495e", "#e91e63", "#00bcd4",
)

AXIS_COLOR = "#666666"
GRID_COLOR = "#dddddd"
TEXT_COLOR = "#333333"

PIE_START = 0.0  # degrees; pie drawing runs counter-clockwise from east


class ChartType:
    """Chart kind names accepted by ``TChart(chart_type=...)``."""

    LINE = "line"
    BAR = "bar"
    HBAR = "hbar"
    SCATTER = "scatter"
    AREA = "area"
    PIE = "pie"

    ALL = (LINE, BAR, HBAR, SCATTER, AREA, PIE)


class _Series:
    """One data series (or, for pie charts, the single labelled slice set)."""

    __slots__ = ("name", "values", "labels", "color")

    def __init__(self, name, values, labels=None, color=None):
        self.name = name
        self.values = list(values)
        self.labels = list(labels) if labels is not None else []
        self.color = color

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


class Chart(Graph):
    """A multi-type plotting element on the Graph user coordinate system.

    Args:
        canvas_size: pixel size of the underlying canvas.
        chart_type: one of :class:`ChartType` ("line" default).
        title: chart title drawn at the top.
        legend: show a legend box (line/bar/hbar/scatter/area).
        grid: draw horizontal+vertical grid lines behind the data.
        axis_labels: ``(x_title, y_title)`` axis captions.
        colors: palette used to cycle series/slice colors.
    """

    __slots__ = (
        "_chart_type", "_title", "_legend", "_grid", "_axis_labels",
        "_palette", "_series", "_auto_range", "_x_range", "_y_range",
        "_pie_labels",
    )

    def __init__(
        self,
        canvas_size=(420, 280),
        chart_type="line",
        title=None,
        legend=True,
        grid=True,
        axis_labels=None,
        colors=PALETTE,
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

    # --- data model -------------------------------------------------------------
    def add_series(self, name, values, labels=None, color=None):
        """Append one series (``[(name, value), ...]`` for pie charts)."""
        if self._chart_type == ChartType.PIE:
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
            self._series.append(_Series(name, values, labels, color))
        return self

    def clear_series(self):
        """Remove every series (chart stays configured)."""
        self._series = []
        return self

    def update_data(self, series_name, values, labels=None):
        """Replace one series' values and redraw (pie: values = pairs)."""
        for series in self._series:
            if series.name == series_name:
                if self._chart_type == ChartType.PIE:
                    pairs = [(str(label), float(value)) for label, value in values]
                    series.values = [value for _label, value in pairs]
                    series.labels = [label for label, _value in pairs]
                else:
                    series.values = list(values)
                    if labels is not None:
                        series.labels = list(labels)
                break
        else:
            raise KeyError(f"no series named {series_name!r}")
        return self.redraw()

    @property
    def series_names(self):
        return [series.name for series in self._series]

    # --- coordinate framing -------------------------------------------------------
    def _data_bounds(self):
        """(x_min, x_max, y_min, y_max) over all series (None for pie)."""
        if self._chart_type == ChartType.PIE or not self._series:
            return None
        count = max(len(series.values) for series in self._series)
        values = [value for series in self._series for value in series.values]
        y_min = min(0.0, min(values))
        y_max = max(values) if values else 1.0
        if y_max == y_min:
            y_max = y_min + 1.0
        pad = (y_max - y_min) * 0.08
        return (0, max(count - 1, 1) if self._chart_type in
                (ChartType.LINE, ChartType.SCATTER) else count,
                y_min - pad, y_max + pad)

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

    # --- palette ------------------------------------------------------------------
    def _color(self, index):
        return self._palette[index % len(self._palette)]

    # --- drawing ------------------------------------------------------------------
    def redraw(self):
        """Recompute framing and render everything from the current data."""
        if self._widget is None:
            return self
        self.widget.delete("all")
        self._pie_labels = []
        if self._chart_type == ChartType.PIE:
            self._draw_pie()
        else:
            self._apply_auto_range()
            self._draw_axes()
            for index, series in enumerate(self._series):
                if self._chart_type == ChartType.LINE:
                    self._draw_line_series(series, self._color(index))
                elif self._chart_type == ChartType.BAR:
                    self._draw_bar_series(series, index)
                elif self._chart_type == ChartType.HBAR:
                    self._draw_hbar_series(series, index)
                elif self._chart_type == ChartType.SCATTER:
                    self._draw_scatter_series(series, self._color(index))
                elif self._chart_type == ChartType.AREA:
                    self._draw_area_series(series, self._color(index))
        self._draw_title()
        if self._legend and self._chart_type != ChartType.PIE:
            self._draw_legend()
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

    def _draw_axes(self):
        left, top, right, bottom = self._plot_rect()
        widget = self._widget
        if self._grid:
            for tick in self._nice_ticks(*self._y_range or (0, 100)):
                y = self._px(tick, "y")
                widget.create_line(
                    left, y, right, y, fill=GRID_COLOR, width=1
                )
            for tick in self._nice_ticks(*self._x_range or (0, 100)):
                x = self._px(tick, "x")
                widget.create_line(
                    x, top, x, bottom, fill=GRID_COLOR, width=1
                )
        widget.create_line(
            left, top, left, bottom, fill=AXIS_COLOR, width=1
        )
        widget.create_line(
            left, bottom, right, bottom, fill=AXIS_COLOR, width=1
        )
        # tick labels
        for tick in self._nice_ticks(*self._y_range or (0, 100)):
            y = self._px(tick, "y")
            widget.create_text(
                left - 6, y, text=self._fmt(tick), anchor="e",
                fill=TEXT_COLOR, font=("TkDefaultFont", 8),
            )
        count = max((len(s.values) for s in self._series), default=0)
        if count:
            category = self._chart_type in (ChartType.BAR, ChartType.HBAR)
            step = (right - left) / max(count, 1)
            labels = self._series[0].labels or [
                str(i + 1) for i in range(count)
            ]
            for i in range(count):
                x = left + step * (i + 0.5) if category else self._px(i, "x")
                widget.create_text(
                    x, bottom + 10, text=labels[i], anchor="n",
                    fill=TEXT_COLOR, font=("TkDefaultFont", 8),
                )
        if self._axis_labels:
            x_title, y_title = self._axis_labels
            if x_title:
                widget.create_text(
                    (left + right) / 2, bottom + 24, text=x_title,
                    anchor="n", fill=TEXT_COLOR, font=("TkDefaultFont", 8),
                )
            if y_title:
                widget.create_text(
                    12, (top + bottom) / 2, text=y_title, angle=90,
                    anchor="w", fill=TEXT_COLOR, font=("TkDefaultFont", 8),
                )

    @staticmethod
    def _fmt(value):
        if float(value).is_integer():
            return str(int(value))
        return f"{value:.2f}".rstrip("0").rstrip(".")

    def _draw_line_series(self, series, color):
        points = [
            (self._px(i, "x"), self._px(v, "y"))
            for i, v in enumerate(series.values)
        ]
        flat = [coordinate for point in points for coordinate in point]
        if len(flat) >= 4:
            self._widget.create_line(
                *flat, fill=color, width=2, smooth=False
            )
        for x, y in points:
            self._widget.create_oval(
                x - 3, y - 3, x + 3, y + 3,
                fill=color, outline=color,
            )

    def _draw_scatter_series(self, series, color):
        for i, value in enumerate(series.values):
            x = self._px(i, "x")
            y = self._px(value, "y")
            size = 4
            self._widget.create_oval(
                x - size, y - size, x + size, y + size,
                fill=color, outline="",
            )

    def _draw_area_series(self, series, color):
        left, top, right, bottom = self._plot_rect()
        baseline = bottom
        points = [(left, baseline)]
        points.extend(
            (self._px(i, "x"), self._px(v, "y"))
            for i, v in enumerate(series.values)
        )
        points.append((self._px(len(series.values) - 1, "x"), baseline))
        flat = [coordinate for point in points for coordinate in point]
        self._widget.create_polygon(
            *flat, fill=color, outline="", stipple="gray50"
        )
        self._draw_line_series(series, color)

    def _draw_bar_series(self, series, series_index):
        left, _top, right, bottom = self._plot_rect()
        count = max(len(s.values) for s in self._series)
        slot = (right - left) / max(count, 1)
        group_count = len(self._series)
        bar_width = slot * 0.7 / group_count
        for i, value in enumerate(series.values):
            x_center = left + slot * (i + 0.5)
            offset = (series_index - (group_count - 1) / 2.0) * bar_width
            x0 = x_center + offset - bar_width / 2
            x1 = x_center + offset + bar_width / 2
            y = self._px(value, "y")
            self._widget.create_rectangle(
                x0, y, x1, bottom,
                fill=self._color(series_index), outline="",
            )

    def _draw_hbar_series(self, series, series_index):
        left, top, right, bottom = self._plot_rect()
        count = max(len(s.values) for s in self._series)
        slot = (bottom - top) / max(count, 1)
        group_count = len(self._series)
        bar_height = slot * 0.7 / group_count
        x_range = self._x_range or (0, 100)
        x_max = x_range[1] or 1.0
        for i, value in enumerate(series.values):
            y_center = top + slot * (i + 0.5)
            offset = (series_index - (group_count - 1) / 2.0) * bar_height
            y0 = y_center + offset - bar_height / 2
            y1 = y_center + offset + bar_height / 2
            length = (
                abs(value) / (x_max or 1.0) * (right - left)
            )
            self._widget.create_rectangle(
                left, y0, left + length, y1,
                fill=self._color(series_index), outline="",
            )

    def _draw_pie(self):
        series = self._series[0] if self._series else None
        if series is None or not series.values:
            return
        width = float(self._canvas_size[0])
        height = float(self._canvas_size[1])
        cx = width * 0.38
        cy = height * 0.55
        radius = min(width * 0.34, height * 0.38)
        total = series.total or 1.0
        angle = PIE_START
        for i, (label, value) in enumerate(series.pairs):
            extent = value / total * 360.0
            # canvas angles go counter-clockwise from 3 o'clock; start at 12
            start = -(angle + extent) + 90
            color = self._color(i)
            self._widget.create_arc(
                cx - radius, cy - radius, cx + radius, cy + radius,
                start=start, extent=max(extent, 0.01),
                style="pieslice", fill=color, outline="white", width=1,
            )
            self._pie_labels.append((label, color))
            angle += extent
        # legend to the right
        legend_x = width * 0.72
        legend_y = cy - radius * 0.7
        for i, (label, color) in enumerate(self._pie_labels):
            y = legend_y + i * 18
            self._widget.create_rectangle(
                legend_x, y - 4, legend_x + 10, y + 6,
                fill=color, outline="",
            )
            self._widget.create_text(
                legend_x + 16, y, text=label, anchor="w",
                fill=TEXT_COLOR, font=("TkDefaultFont", 8),
            )

    def _draw_title(self):
        if not self._title:
            return
        width = float(self._canvas_size[0])
        self._widget.create_text(
            width / 2, 12, text=self._title, anchor="n",
            fill=TEXT_COLOR, font=("TkDefaultFont", 10, "bold"),
        )

    def _draw_legend(self):
        if not self._series:
            return
        widget = self._widget
        width = float(self._canvas_size[0])
        box_width = 14
        text_width = 0
        for series in self._series:
            text_width = max(text_width, len(series.name))
        box_w = box_width + text_width * 7 + 18
        box_h = 10 + 16 * len(self._series)
        x1 = width - box_w - 8
        y0 = 22
        widget.create_rectangle(
            x1, y0, x1 + box_w, y0 + box_h,
            fill="white", outline=GRID_COLOR,
        )
        for i, series in enumerate(self._series):
            y = y0 + 10 + i * 16
            widget.create_rectangle(
                x1 + 6, y - 4, x1 + 6 + box_width, y + 6,
                fill=self._color(i), outline="",
            )
            widget.create_text(
                x1 + 6 + box_width + 6, y, text=series.name, anchor="w",
                fill=TEXT_COLOR, font=("TkDefaultFont", 8),
            )
