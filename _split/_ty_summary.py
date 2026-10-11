#!/usr/bin/env python3
"""Aggregate _ty_probe_out.txt by kind/code and file."""
import collections
import re

lines = open("_split/_ty_probe_out.txt", encoding="utf-8").read().splitlines()
kinds = collections.Counter()
files = collections.Counter()
codes = collections.Counter()
total = 0
for line in lines:
    match = re.match(r"([a-z\\]+\.py):(\d+):(\d+): (\w+)\[([^\]]*)\] (.*)", line)
    if match:
        total += 1
        path, _l, _c, kind, code, _msg = match.groups()
        kinds[kind] += 1
        codes[(kind, code)] += 1
        files[path.rsplit("\\", 1)[-1]] += 1
print("total:", total)
print("by kind:", dict(kinds))
for (kind, code), count in codes.most_common(12):
    print(f"  {count:3d}  {kind}/{code}")
for name, count in files.most_common(12):
    print(f"{count:4d}  {name}")
