#!/usr/bin/env python3
"""Generate a 16x16 P4 badge icon for the demo's table/tree row icons."""
import base64
import struct
import zlib

sys_path_note = None


def write_png(width, height, rows):
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


def main():
    size = 16
    radius = 4
    top = (70, 140, 225)
    bottom = (26, 60, 110)
    rows = []
    for y in range(size):
        row = []
        t = y / float(size - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        for x in range(size):
            dx = min(x, size - 1 - x)
            dy = min(y, size - 1 - y)
            inside = True
            if dx < radius and dy < radius:
                inside = (radius - dx) ** 2 + (radius - dy) ** 2 <= radius ** 2
            if inside:
                row.extend((r, g, b, 255))
            else:
                row.extend((0, 0, 0, 0))
        rows.append(row)
    png = write_png(size, size, rows)
    encoded = base64.b64encode(png).decode("ascii")
    with open("_split/icon16_b64.txt", "w") as handle:
        handle.write(encoded)
    print("16px icon:", len(png), "bytes ->", encoded[:60], "...")


if __name__ == "__main__":
    main()
