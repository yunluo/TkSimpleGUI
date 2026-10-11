<p align="center">
  <img src="https://raw.githubusercontent.com/PySimpleGUI/PySimpleGUI/master/images/for_readme/Logo%20with%20text%20for%20GitHub%20Top.png" alt="User Interfaces for Humans">
</p>

# PySimpleGUI4

**PySimpleGUI** is a Python library that simplifies the process of creating graphical user interfaces (GUIs). It abstracts away the complexity of underlying frameworks like Tkinter, offering a beginner-friendly, high-level API.

---

## What's New in v4.80.7

This version introduces a **modular architecture** for better maintainability and Python 3.7+ compatibility:

### Directory Structure

```
PySimpleGUI4/
├── src/PySimpleGUI4/            # Object oriented package (import as `PySimpleGUI4`)
│   ├── __init__.py              # Public API + PySimpleGUI style aliases
│   ├── _version.py              # Version information
│   ├── constants.py             # Immutable constants + enums
│   ├── _theme_data.py           # Generated theme table (160 themes)
│   ├── _theming.py              # ThemeManager (encapsulated look & feel)
│   ├── settings.py              # Settings singleton + set_options/get_options
│   ├── utils.py                 # rgb, Timer, platform detection, DPI awareness
│   ├── event.py                 # PySimpleEvent + singleton_window
│   ├── actions.py               # Action / ActionList (TActionList analog)
│   ├── user_settings.py         # UserSettings (JSON persistence, QSettings analog)
│   ├── i18n.py                  # Dictionary translation (Qt tr() analog)
│   ├── animation.py             # fade/slide/progress animation helpers
│   ├── popup.py                 # Popup dialogs built on Window itself
│   ├── elements/
│   │   ├── base.py              # Element(ABC) hierarchy + right-click menus + grid engine
│   │   ├── widgets.py           # Text, Input(+validation), Combo, Listbox, Spin,
│   │   │                        #   Checkbox, CheckList, Radio, Slider, Multiline,
│   │   │                        #   Output, ProgressBar
│   │   ├── buttons.py           # Button (+ browse variants, toggle, image, Action)
│   │   ├── media.py             # Image, Canvas, Graph (figure handles), Shape
│   │   ├── containers.py        # Frame, Column, Splitter, ScrollableColumn, Toolbar,
│   │   │                        #   LabeledEdit, KeyValueEditor, FlowPanel, Tab, TabGroup, Menu
│   │   ├── calendar.py          # Calendar (embedded month view)
│   │   ├── data.py              # Table (sort/edit/bind/icons), Tree (item icons)
│   │   └── misc.py              # StatusBar, separators, Sizegrip
│   └── window/
│       ├── window.py            # Window: read loop, layout engine, timers, clipboard
│       └── system_tray.py       # SystemTray (icon, menu, balloon, events)
├── _split/                      # Baseline toolchain (reference & theme extraction)
├── tests/test_package.py        # unittest suite (90 tests)
├── demo.py                      # Full feature showcase (six tabs, --smoke self-test)
├── todo.md                      # Roadmap (Qt/Delphi gap plan, all batches done)
├── pyproject.toml               # Project configuration
└── README.md                    # This file
```

### Design

- **Object oriented** - every element derives from `Element` (ABC) with
  `InputElement` / `ContainerElement` intermediate bases; the window builds
  layouts through polymorphism, no giant type-checking chains
- **Encapsulated** - `__slots__` everywhere, private attributes, `@property`
  accessors; the mutable look & feel and options state live in the
  `ThemeManager` and `Settings` singletons instead of module globals
- **System native by default** - until you call `sg.theme("...")` no colors
  are overridden and ttk widgets use the operating system's native theme
- **Python 3.7+ compatible** - zero third-party dependencies, Tkinter/ttk only

### Key Improvements

1. **PEP8 Compliance** - Code follows Python style guidelines
2. **Python 3.7+ Compatible** - No third-party dependencies
3. **Type Annotations** - All public functions have type hints
4. **Modular Design** - Easier to maintain and extend
5. **Backward Compatible** - All original aliases preserved

---

## Installation

```bash
pip install PySimpleGUI4
```

## Quick Start

```python
import PySimpleGUI4 as sg

layout = [
    [sg.Text("Hello, PySimpleGUI4!")],
    [sg.Button("OK"), sg.Button("Cancel")]
]

window = sg.Window("My Window", layout)

while True:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, "Cancel"):
        break
    print("Event:", event)

window.close()
```

---

## Features

- **Beginner-Friendly**: Intuitive syntax
- **Rich Component Library**: Buttons, inputs, sliders, progress bars, tables, and more
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Dynamic Updates**: Real-time GUI element updates
- **Theming**: Built-in color themes

---

## Version Info

- **Version**: 4.80.7
- **Python**: >= 3.7
- **License**: GPL-3.0-or-later
