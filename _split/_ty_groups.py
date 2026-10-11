#!/usr/bin/env python3
"""Group ty diagnostics by file/kind/normalized message."""
import collections
import re

lines = open("_split/_ty_probe_out.txt", encoding="utf-8").read().splitlines()
groups = collections.Counter()
for line in lines:
    match = re.match(r"src..([a-z_]+\.py):\d+:\d+: error\[(\w[\w-]*)\] (.+)", line)
    if match:
        key = (
            match.group(1),
            match.group(2),
            re.sub(r"`[^`]+`", "X", match.group(3))[:55],
        )
        groups[key] += 1
for (name, kind, message), count in groups.most_common(40):
    print(f"{count:3d}  {name:16s} {kind:26s} {message}")
