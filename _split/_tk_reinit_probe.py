#!/usr/bin/env python3
"""Check: is creating a second tk.Tk() after destroying the last one safe?"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import tkinter as tk

print("root1 create", flush=True)
root1 = tk.Tk()
root1.withdraw()
print("root1 destroy", flush=True)
root1.destroy()
print("root2 create", flush=True)
root2 = tk.Tk()
root2.withdraw()
print("root2 update", flush=True)
root2.update()
print("root2 destroy", flush=True)
root2.destroy()
print("SURVIVED", flush=True)
