#!/usr/bin/env python3
"""Raw ty probe: write output streams to files for inspection."""
import subprocess

run = subprocess.run(
    [r"D:\bin\ty.exe", "check", "src", "--python-version", "3.7",
     "--output-format", "concise"],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
)
with open("_split/_ty_probe_out.txt", "w", encoding="utf-8") as handle:
    handle.write("=== RC: {}\n=== STDOUT ({} chars) ===\n".format(
        run.returncode, len(run.stdout)))
    handle.write(run.stdout)
    handle.write("\n=== STDERR ({} chars) ===\n".format(len(run.stderr)))
    handle.write(run.stderr)
print("written")
