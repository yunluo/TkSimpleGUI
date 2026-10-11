#!/usr/bin/env python3
"""Decode the generated logo PNGs and write a 6x upscaled preview."""
import tkinter as tk

data = open("_split/logo_b64.txt", "rb").read().split(b"\n")

import base64
open("_split/_logo64.png", "wb").write(base64.b64decode(data[1]))
open("_split/_logo32.png", "wb").write(base64.b64decode(data[4]))

root = tk.Tk()
root.withdraw()
big = tk.PhotoImage(file="_split/_logo64.png").zoom(6, 6)
big.write("_split/_logo64_big.png")
small = tk.PhotoImage(file="_split/_logo32.png").zoom(6, 6)
small.write("_split/_logo32_big.png")
root.destroy()
print("previews written")
