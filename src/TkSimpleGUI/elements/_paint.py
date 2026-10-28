#!/usr/bin/env python3
"""Shared painting toolkit for the canvas-drawn elements.

The self-drawn widgets (TTag, TBadge, TAvatar, TSteps, TRate, ...) all need the
same few things Tk does not offer out of the box:

- **Concrete colors for the active theme.** :func:`palette` resolves the
  theme manager into hex values (surface / ink / muted / accent / border /
  track). It also works for the native look: platform defaults are sampled
  from throwaway widgets and normalized with ``winfo_rgb``, so even system
  colors ("SystemButtonFace") can be blended into readable shades.
- **Rounded shapes.** Tk has no rounded rectangle; :func:`rounded_polygon`
  and :func:`capsule` draw the classic smooth-polygon forms.
- **Small vector glyphs.** :func:`cross`, :func:`check_mark` and
  :func:`triangle` build the close "x", the check mark and trend arrows.
- **Polygon clipping** for the half rating stars (:func:`clip_left_half`).
- **TText measuring** (:func:`measure_text`) so capsules can size to their
  label in any font, including CJK.

Semantic status colors (info / success / warning / danger) follow the
Element Plus palette; they are deliberately *not* theme derived — a red
error must stay red in every palette — but every element accepts an
explicit override.
"""

import math
import tkinter as tk
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .. import _theming as theme_mod
from .._theming import _blend as blend
from ..constants import FontSpec

Point = Tuple[float, float]
Color = str
ColorMap = Dict[Color, Color]

# semantic status colors (Element Plus palette); overridable per element
INFO = "#909399"
SUCCESS = "#67c23a"
WARNING = "#e6a23c"
DANGER = "#f56c6c"

_STATUS_COLORS = {
    "info": INFO,
    "success": SUCCESS,
    "warning": WARNING,
    "error": DANGER,
    "danger": DANGER,
}

_PIL = None  # cached (Image, ImageDraw), or False when Pillow is missing


def pil_modules():
    """(Image, ImageDraw) when Pillow is installed, else False (cached)."""
    global _PIL
    if _PIL is None:
        try:
            from PIL import Image, ImageDraw

            _PIL = (Image, ImageDraw)
        except Exception:  # any import failure: fall back to pure Tk
            _PIL = False
    return _PIL


def status_color(status: str, colors: ColorMap) -> Color:
    """The color for a status name; ``"primary"`` follows the theme accent."""
    key = str(status or "info").lower()
    if key == "primary":
        return colors["accent"]
    return _STATUS_COLORS.get(key, INFO)


# --- color resolution ---------------------------------------------------------
def to_hex(widget: tk.Misc, color: Optional[Color], fallback: Color = "#808080") -> Color:
    """Best effort ``#rrggbb`` for any Tk color (named / system colors).

    ``winfo_rgb`` resolves names Tk knows ("SystemButtonFace", "gray70")
    to real channel values; hex input is normalized, anything else falls
    back so callers always receive a blendable color.
    """
    rgb = theme_mod._parse_hex(color)
    if rgb is not None:
        return "#{:02x}{:02x}{:02x}".format(*rgb)  # noqa: UP032  (3.7 style)
    if isinstance(color, str) and widget is not None:
        try:
            red, green, blue = widget.winfo_rgb(color)
            return "#{:02x}{:02x}{:02x}".format(  # noqa: UP032
                red >> 8, green >> 8, blue >> 8
            )
        except Exception:
            return fallback
    return fallback


def _native_color(widget: tk.Misc, widget_class: Any, option: Any, fallback: Color) -> Color:
    """Sample a platform default value (e.g. a plain tk.Frame background)."""
    try:
        value = theme_mod.native_widget_colors(widget_class, widget, (option,))[option]
    except Exception:
        return fallback
    return to_hex(widget, value, fallback)


def palette(widget: tk.Misc, surface: Any = None, ink: Any = None) -> ColorMap:
    """Resolve the active theme into concrete, blendable hex colors.

    Keys: ``surface`` (background to draw on), ``ink`` (primary text),
    ``muted`` (secondary text), ``accent`` / ``accent_ink`` (theme accent
    and the text color that reads on it), ``border``, ``track`` (inactive
    fills) and ``subtle`` (a barely-there fill for troughs and stripes).

    ``surface`` / ``ink`` override the theme values (explicit per-element
    colors); under the native look the platform defaults are sampled so
    the palette is never a guess.
    """
    manager = theme_mod.theme_manager
    surface_value = surface if surface is not None else manager.effective_background()
    if surface_value is None:
        surface_hex = _native_color(widget, tk.Frame, "background", "#f0f0f0")
    else:
        surface_hex = to_hex(widget, surface_value, "#f0f0f0")
    ink_value = ink if ink is not None else manager.text_color
    if ink_value is None or theme_mod._is_system_default(ink_value):
        ink_hex = _native_color(widget, tk.Label, "foreground", "#1e2228")
    else:
        ink_hex = to_hex(widget, ink_value, "#1e2228")
    accent_hex = to_hex(widget, manager.accent_color() or "#3a7bd5", "#3a7bd5")
    return {
        "surface": surface_hex,
        "ink": ink_hex,
        "muted": blend(ink_hex, surface_hex, 0.45),
        "accent": accent_hex,
        "accent_ink": theme_mod.contrast_on(accent_hex),
        "border": blend(ink_hex, surface_hex, 0.78),
        "track": blend(ink_hex, surface_hex, 0.88),
        "subtle": blend(ink_hex, surface_hex, 0.945),
    }


def tint(color: Color, colors: ColorMap, ratio: float = 0.86) -> Color:
    """A soft wash of ``color`` over the theme surface (light "effect")."""
    return blend(color, colors["surface"], ratio)


def shade(color: Color, colors: ColorMap, ratio: float = 0.30) -> Color:
    """``color`` mixed toward the theme ink — a readable text tint."""
    return blend(color, colors["ink"], ratio)


def ease_out_cubic(t: float) -> float:
    """Easing curve from 0 to 1 — fast start, soft landing; input clamped."""
    t = min(max(float(t), 0.0), 1.0)
    return 1.0 - (1.0 - t) ** 3


def tween_color(widget: tk.Misc, start: Color, end: Color, t: float) -> Color:
    """The color at linear progress ``t`` (0..1) between ``start`` and ``end``.

    Accepts anything :func:`to_hex` understands (hex, Tk color names,
    native system colors — those are sampled on ``widget``); values that
    cannot be parsed snap to ``start``. Linear by design — pair with
    :func:`ease_out_cubic` when the motion should feel eased.
    """
    ratio = min(max(float(t), 0.0), 1.0)
    return blend(to_hex(widget, start), to_hex(widget, end), ratio)


def themed_canvas(master: tk.Misc, width: int, height: int, surface: Color) -> tk.Canvas:
    """A flat canvas without highlight ring, on the given surface color."""
    return tk.Canvas(
        master,
        width=int(width),
        height=int(height),
        highlightthickness=0,
        bd=0,
        background=surface,
    )


def measure_text(widget: tk.Misc, text: str, font: Optional[FontSpec]) -> int:
    """Pixel width of ``text`` in ``font`` (falls back to an estimate)."""
    try:
        from tkinter import font as tkfont

        return tkfont.Font(root=widget, font=font).measure(text)
    except Exception:
        return len(str(text)) * 8


# --- shapes -------------------------------------------------------------------
def rounded_polygon(
    canvas: tk.Canvas,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    radius: float,
    **kwargs: Any) -> int:
    """A closed rounded rectangle as a smooth canvas polygon.

    Tk has no native rounded rectangle; the smooth-polygon approximation
    below is the classic trick (it is what TRoundButton has always used).
    """
    points = [
        x0 + radius, y0,
        x1 - radius, y0,
        x1, y0,
        x1, y0 + radius,
        x1, y1 - radius,
        x1, y1,
        x1 - radius, y1,
        x0 + radius, y1,
        x0, y1,
        x0, y0 + radius,
        x0, y0,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def capsule(canvas: tk.Canvas, x0: float, y0: float, x1: float, y1: float, **kwargs: Any) -> int:
    """A fully rounded (pill) shape spanning the given box."""
    radius = min(abs(x1 - x0), abs(y1 - y0)) / 2.0
    return rounded_polygon(canvas, x0, y0, x1, y1, radius, **kwargs)


def cross(canvas: tk.Canvas, cx: float, cy: float, size: float, **kwargs: Any) -> List[int]:
    """An "x" close glyph centered on (cx, cy) with the given extent."""
    half = size / 2.0
    return [
        canvas.create_line(cx - half, cy - half, cx + half, cy + half, **kwargs),
        canvas.create_line(cx - half, cy + half, cx + half, cy - half, **kwargs),
    ]


def check_mark(canvas: tk.Canvas, cx: float, cy: float, size: float, **kwargs: Any) -> int:
    """A round-capped check mark sized to fit ``size``."""
    half = size / 2.0
    coords = [
        cx - half, cy,
        cx - size * 0.10, cy + half * 0.66,
        cx + half, cy - half * 0.60,
    ]
    return canvas.create_line(
        coords, capstyle="round", joinstyle="round", **kwargs
    )


def triangle(
    canvas: tk.Canvas,
    cx: float,
    cy: float,
    size: float,
    direction: str = "up",
    **kwargs: Any) -> int:
    """A filled trend arrow pointing ``up`` or ``down``."""
    half = size / 2.0
    if str(direction).lower() == "down":
        points = [cx, cy + half, cx - half, cy - half, cx + half, cy - half]
    else:
        points = [cx, cy - half, cx - half, cy + half, cx + half, cy + half]
    return canvas.create_polygon(points, **kwargs)


def star_points(cx: float, cy: float, outer: Any, inner: Any, points: int = 5,
                rotation: float = 90.0) -> List[Point]:
    """The vertex list of a star polygon (alternating outer/inner radii).

    Coordinates are screen oriented (y grows downward); the default
    rotation puts the first, outer vertex straight up.
    """
    vertices: List[Point] = []
    step = 360.0 / (points * 2)
    angle = rotation
    for index in range(points * 2):
        radius = outer if index % 2 == 0 else inner
        radians = math.radians(angle)
        vertices.append(
            (cx + radius * math.cos(radians), cy - radius * math.sin(radians))
        )
        angle += step
    return vertices


def clip_left_half(points: Sequence[Point], limit: Any = None) -> List[Point]:
    """Clip a polygon to the left of a vertical line (Sutherland-Hodgman).

    ``limit`` defaults to the horizontal center of the polygon's bounding
    box — the exact half of a symmetric star. Returns the clipped vertex
    list (empty when the polygon lies fully to the right).
    """
    if limit is None:
        left = min(point[0] for point in points)
        right = max(point[0] for point in points)
        limit = (left + right) / 2.0
    clipped: List[Point] = []
    count = len(points)
    for index in range(count):
        current = points[index]
        following = points[(index + 1) % count]
        current_inside = current[0] <= limit
        following_inside = following[0] <= limit
        if current_inside:
            clipped.append((current[0], current[1]))
        if current_inside != following_inside:
            span = following[0] - current[0]
            if abs(span) > 1e-9:
                ratio = (limit - current[0]) / span
                clipped.append(
                    (limit, current[1] + (following[1] - current[1]) * ratio)
                )
    return clipped


def flatten(points: Sequence[Point]) -> List[float]:
    """``[(x, y), ...]`` -> ``[x, y, x, y, ...]`` for create_polygon/line."""
    flat: List[float] = []
    for x, y in points:
        flat.append(x)
        flat.append(y)
    return flat


def as_float(value: Any, fallback: float = 0.0) -> float:
    """Coerce to float, tolerating None and unparsable strings."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


# --- Pillow font files --------------------------------------------------------
_FONT_DIRS = (
    "C:\\Windows\\Fonts",
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    "/System/Library/Fonts",
    "/Library/Fonts",
)

_FONT_FILES = (
    "segoeui.ttf", "arial.ttf", "calibri.ttf", "verdana.ttf", "tahoma.ttf",
    "msyh.ttc", "simsun.ttc", "DejaVuSans.ttf", "LiberationSans-Regular.ttf",
    "Helvetica.ttc",
)

_FONT_CACHE: Dict[str, Any] = {}


def system_font_file(family: Any = None):
    """Best effort path to a TrueType file for Pillow text rendering.

    Pillow renders text from font *files*; Tk fonts are not files. The
    lookup walks the platform font directories for the requested family
    (normalized name match) and then for a handful of common fallbacks.
    ``None`` means "no usable file" — callers keep their pure Tk path.
    """
    import os

    key = str(family or "").lower()
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    result = None
    if family:
        stem = "".join(ch for ch in key if ch.isalnum())
        for directory in _FONT_DIRS:
            if not os.path.isdir(directory):
                continue
            for name in sorted(os.listdir(directory)):
                if not name.lower().endswith((".ttf", ".ttc", ".otf")):
                    continue
                candidate = os.path.join(directory, name)
                if not os.path.isfile(candidate):
                    continue
                lowered = "".join(ch for ch in name.lower() if ch.isalnum())
                if stem and lowered.startswith(stem):
                    result = candidate
                    break
            if result is not None:
                break
    if result is None:
        for directory in _FONT_DIRS:
            if not os.path.isdir(directory):
                continue
            for name in _FONT_FILES:
                candidate = os.path.join(directory, name)
                if os.path.isfile(candidate):
                    result = candidate
                    break
            if result is None:
                for name in sorted(os.listdir(directory)):
                    if name.lower().endswith((".ttf", ".ttc")):
                        candidate = os.path.join(directory, name)
                        if os.path.isfile(candidate):
                            result = candidate
                            break
            if result is not None:
                break
    _FONT_CACHE[key] = result
    return result
