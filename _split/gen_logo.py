#!/usr/bin/env python3
"""Generate the TkSimpleGUI default window icon (replaces the Tk feather).

Pure stdlib: draws a rounded-square blue gradient badge with a white "T4"
monogram (64x64) and a white "T" mark (32x32), encodes both as PNG and
writes their base64 to ``_split/logo_b64.txt`` for pasting into
``constants.py``.
"""

import base64
import struct
import zlib

# --- 5x7 pixel glyphs ---------------------------------------------------------
GLYPHS = {
    "T": (
        "11111",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
    ),
    "k": (
        "10001",
        "10010",
        "10100",
        "11000",
        "10100",
        "10010",
        "10011",
    ),
    "4": (
        "00010",
        "00110",
        "01010",
        "10010",
        "11111",
        "00010",
        "00010",
    ),
}

GRADIENT_TOP = (70, 140, 225)
GRADIENT_BOTTOM = (26, 60, 110)
WHITE = (255, 255, 255, 255)
SHADOW = (16, 38, 72, 255)


def write_png(width, height, rows):
    """Encode 8-bit RGBA rows (top down, each a flat byte list) into a PNG."""
    raw = b"".join(b"\x00" + bytes(row) for row in rows)

    def chunk(tag, data):
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def inside_rounded(x, y, size, radius):
    dx = min(x, size - 1 - x)
    dy = min(y, size - 1 - y)
    if dx < radius and dy < radius:
        return (radius - dx) ** 2 + (radius - dy) ** 2 <= radius ** 2
    return True


def gradient(y, height):
    t = y / float(height - 1)
    return tuple(
        int(GRADIENT_TOP[i] + (GRADIENT_BOTTOM[i] - GRADIENT_TOP[i]) * t)
        for i in range(3)
    )


def draw_icon(size, text, scale, radius):
    """Render the badge; ``text`` is drawn centered at ``scale`` px per dot."""
    glyph_width = 5 * scale
    total_width = len(text) * glyph_width + (len(text) - 1) * scale
    total_height = 7 * scale
    x0 = (size - total_width) // 2
    y0 = (size - total_height) // 2
    rows = []
    for y in range(size):
        row = []
        for x in range(size):
            if not inside_rounded(x, y, size, radius):
                row.extend((0, 0, 0, 0))
                continue
            r, g, b = gradient(y, size)
            row.extend((r, g, b, 255))
        rows.append(row)
    for offset, color in ((scale // 3, SHADOW), (0, WHITE)):
        if offset == 0 and color is WHITE:
            ox = oy = 0
        else:
            ox = oy = offset
        pen_x = x0 + ox
        for char in text:
            glyph = GLYPHS[char]
            for gy, line in enumerate(glyph):
                for gx, dot in enumerate(line):
                    if dot != "1":
                        continue
                    for py in range(scale):
                        for px in range(scale):
                            x = pen_x + gx * scale + px
                            y = y0 + oy + gy * scale + py
                            if 0 <= x < size and 0 <= y < size:
                                rows[y][4 * x:4 * x + 4] = color
            pen_x += glyph_width + scale
    return write_png(size, size, rows)


def main():
    outputs = []
    for name, png in (
        ("DEFAULT_BASE64_ICON (64px)", draw_icon(64, "Tk", 5, 13)),
        ("DEFAULT_BASE64_ICON_SMALL (32px)", draw_icon(32, "T", 3, 7)),
    ):
        encoded = base64.b64encode(png)
        outputs.append((name, len(png), encoded))
    with open("_split/logo_b64.txt", "wb") as handle:
        for name, size, encoded in outputs:
            handle.write("# {} - {} bytes\n".format(name, size).encode("ascii"))
            handle.write(encoded + b"\n\n")
    for name, size, encoded in outputs:
        print("{}: {} png bytes, {} b64 chars".format(name, size, len(encoded)))


if __name__ == "__main__":
    main()
