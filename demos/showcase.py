#!/usr/bin/env python3
"""TkSimpleGUI full-featured showcase (current standard style).

Demonstrates the **recommended style**:
- ``window.run()`` -- the root object starts the app, zero user loop
- ``@ts.bind_event`` + ``on_*`` functions -- dispatched by the built-in
  default event manager (no explicit imports)
- ``Action`` -- actions shared between menus, toolbars and shortcuts
- ``parent=`` -- window hierarchy (child window demo, cascading close)
- T-prefix naming, Toast, RoundButton, TextProgressBar, slider bubbles...

Run::

    python demos/showcase.py            # interactive mode
    python demos/showcase.py --smoke    # self-test: pump events ~2s, then exit

Exit behaviour: the title bar X is *not* a hard quit -- it asks for
confirmation first. The File > Exit menu entry is the hard-quit path.
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import TkSimpleGUI as ts  # noqa: E402

# 16x16 badge (table row icons / tree node icons)
ICON16 = (
    b"iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAiUlEQVR42mNgQANuPQ//48MM"
    b"uIBz283/pGAUzQ6NF/+Tg+EG2Nac+k8OBmu2Kjv0nxLMYF646z8lmMEkZ/N/SjCDYdrq/5Rg"
    b"Br3Exf8pwQzaMXP+U4IZNMKm/KcEM6gG9vynBIPTgpJP639yMDwlyrvV/icHo+QHGcfS/6Rg"
    b"nLlSyibvPz6Mrh4AeY7yRAY4AssAAAAASUVORK5CYII="
)

_STOPWATCH = {"start": None}
_TRAY = {"obj": None}
_PREFS = ts.UserSettings("demo.json")

# runtime shared state (handlers pass data through this)
_state = {
    "window": None,          # main window (filled by build())
    "figure_last": None,
    "figure_count": 0,
    "tree_counter": 0,
    "about_window": None,    # standalone About child (parent hierarchy demo)
}


def log(text, color=None):
    """Append one line to the bottom event log (optionally colored)."""
    window = _state["window"]
    if window is not None and "-LOG-" in window:
        window["-LOG-"].print(time.strftime("[%H:%M:%S] ") + text, text_color=color)


def require_window():
    """The window a handler receives IS the main window (first arg everywhere)."""
    return _state["window"]


# ---------------------------------------------------------------- tab layouts --
def tab_inputs():
    band_top = ts.Column([
        [ts.Column([[ts.TText("Integer validation (digits only)")],
                    [ts.TInput("", key="-IN-NUM-", size=(12, 1), validate="key",
                              validate_command=ts.validate_integer,
                              enable_events=True)]]),
         ts.Column([[ts.TText("Password")],
                    [ts.TInput("", key="-IN-PASS-", size=(12, 1), password_char="*")],
                    [ts.TCheckbox("Show password", key="-CB-SHOW-", enable_events=True)]]),
         ts.Column([[ts.TLabeledEdit("Username", "yunluo", key="-IN-USER-")],
                    [ts.TButton("Submit form", key="-SUBMIT-")]]),
         ts.Column([[ts.TText("Spin")],
                    [ts.TSpin([str(n) for n in range(1, 11)], initial_value="5",
                              key="-SP-", enable_events=True)]])],
    ])
    band_slider = ts.Column([
        [ts.TText("Slider drives the progress bar (show_value bubble while dragging):")],
        [ts.TSlider((0, 100), default_value=30, key="-SL-",
                    enable_events=True, size=(18, 15), show_value=True),
         ts.TProgressBar(100, current_value=30, size=(20, 12), key="-PB-SL-")],
    ])
    band_multiline = ts.Column([
        [ts.TMultiline("Multiline area (undo/redo, colored output, find/replace)\n",
                       key="-ML-", size=(56, 5))],
        [ts.TButton("Color output", key="-B-COLOR-"), ts.TButton("Undo", key="-B-UNDO-"),
         ts.TButton("Redo", key="-B-REDO-"), ts.TButton("Find", key="-B-FIND-"),
         ts.TButton("Replace", key="-B-REPLACE-"), ts.TButton("Clear", key="-B-CLEAR-ML-")],
    ])
    return [[band_top], [band_slider], [band_multiline]]


def tab_selection():
    band = ts.Column([
        [ts.Column([[ts.TText("Combo")],
                    [ts.TCombo(["Red", "Green", "Blue"], default_value="Red",
                              key="-CMB-", enable_events=True)],
                    [ts.TText("OptionMenu")],
                    [ts.TOptionMenu(["First", "Second", "Third"], key="-OPT-",
                                   enable_events=True)],
                    [ts.TText("Spin")],
                    [ts.TSpin(["Low", "Medium", "High"], initial_value="Medium",
                             key="-SP2-", enable_events=True)]],
                   ),
         ts.Column([[ts.TText("Listbox (multi-select)")],
                    [ts.TListbox(["Item one", "Item two", "Item three", "Item four"],
                                size=(14, 4), select_mode=ts.SelectMode.EXTENDED,
                                key="-LB-", enable_events=True)]]),
         ts.Column([[ts.TText("Checkbox")],
                    [ts.TCheckbox("Check A", key="-CBA-", enable_events=True)],
                    [ts.TCheckbox("Check B", key="-CBB-", enable_events=True)]]),
         ts.Column([[ts.TText("CheckList")],
                    [ts.TCheckList(["Melon", "Apple", "Banana"],
                                  default_checked=["Apple"], key="-CKL-",
                                  enable_events=True)],
                    [ts.TButton("All", key="-B-CKALL-"),
                     ts.TButton("None", key="-B-CKNONE-")]]),
         ts.Column([[ts.TText("Radio (exclusive)")],
                    [ts.TRadio("Plan 1", "plan", default=True, key="-R1-",
                              enable_events=True)],
                    [ts.TRadio("Plan 2", "plan", key="-R2-", enable_events=True)],
                    [ts.TRadio("Plan 3", "plan", key="-R3-", enable_events=True)]])],
    ])
    return [[band]]


def tab_data():
    records = [
        {"Name": "Yunluo", "Age": 30, "City": "Shenzhen"},
        {"Name": "Ming", "Age": 24, "City": "Hangzhou"},
        {"Name": "Qiang", "Age": 36, "City": "Chengdu"},
        {"Name": "Mei", "Age": 28, "City": "Shanghai"},
    ]
    table = ts.TTable([], headings=[], key="-TB-", enable_edit=True,
                      row_icons=[ICON16, ICON16, ICON16, ICON16], num_rows=5,
                      auto_size_columns=False, col_widths=[10, 8, 10])
    table.bind(records)
    tree = ts.TTree(headings=["Node"], show_headings=False, num_rows=6, key="-TREE-")
    kv = ts.TKeyValueEditor([("Host", "localhost"), ("Port", "5432")], key="-KV-")
    band = ts.Column([
        [ts.Column([[ts.TText("Table: click header sorts / double-click edits"
                              " / row icons / drag separator")],
                    [table],
                    [ts.TButton("Rebind data", key="-B-REBIND-"),
                     ts.TText("Selected record:"),
                     ts.TText("", key="-T-REC-", size=(22, 1))]]),
         ts.Column([[ts.TText("Tree (icons / groups / summary rows)")],
                    [tree],
                    [ts.TButton("Add group", key="-B-ADDGRP-"),
                     ts.TButton("Add node", key="-B-ADD-"),
                     ts.TButton("Delete node", key="-B-DEL-")]]),
         ts.Column([[ts.TText("KeyValue editor (TValEdit)")],
                    [kv],
                    [ts.TButton("Read values", key="-B-KVGET-")]])],
    ])
    return [[band]]


def tab_graphics():
    graph = ts.TGraph((320, 160), (0, 0), (100, 54), key="-GRAPH-",
                      enable_events=True, background_color="#ffffff")
    # --- new: TChart gallery (six chart types, one data model) ---------------
    charts = {}
    specs = [
        ("-CH-LINE-", "line", "Line", "Revenue"),
        ("-CH-BAR-", "bar", "Bar", "Units"),
        ("-CH-AREA-", "area", "Area", "Trend"),
        ("-CH-SCATTER-", "scatter", "Scatter", "Samples"),
        ("-CH-HBAR-", "hbar", "HBar", "Speed"),
        ("-CH-PIE-", "pie", "Pie", "Share"),
    ]
    for key, kind, _label, title in specs:
        chart = ts.TChart((300, 190), chart_type=kind, title=title,
                          legend=(kind != "pie"), key=key,
                          enable_events=True, background_color="#ffffff")
        charts[key] = chart
    charts["-CH-LINE-"].add_series("2024", [12, 34, 28, 41, 26, 38],
                                   labels=["Jan", "Feb", "Mar", "Apr", "May", "Jun"])
    charts["-CH-LINE-"].add_series("2025", [22, 30, 38, 35, 31, 44])
    charts["-CH-BAR-"].add_series("East", [12, 30, 8, 24],
                                  labels=["Q1", "Q2", "Q3", "Q4"])
    charts["-CH-BAR-"].add_series("West", [9, 24, 16, 20])
    charts["-CH-AREA-"].add_series("load", [4, 6, 5, 9, 7, 11, 8])
    charts["-CH-SCATTER-"].add_series("pts", [1, 5, 3, 8, 2, 7, 4, 9])
    charts["-CH-HBAR-"].add_series("speed", [40, 65, 30, 80],
                                   labels=["a", "b", "c", "d"])
    charts["-CH-PIE-"].add_series("share",
                                  [("alpha", 30), ("beta", 20), ("gamma", 50)])
    for chart in charts.values():
        chart.redraw()
    return [
        [ts.Column([[ts.TText("TChart -- line / bar / area / scatter / hbar / pie"
                              " (click the buttons to live-update)")],
                    [ts.TButton("Update line data", key="-B-CHUPD-"),
                     ts.TButton("Add bar series", key="-B-CHADD-"),
                     ts.TButton("Reseed pie", key="-B-CHPIE-")],
                    [charts["-CH-LINE-"], charts["-CH-BAR-"],
                     charts["-CH-AREA-"]],
                    [charts["-CH-SCATTER-"], charts["-CH-HBAR-"],
                     charts["-CH-PIE-"]]])],
        [ts.Column([[ts.TText("TGraph (user coords + figure handles) -- click the canvas")],
                    [graph],
                    [ts.TButton("Circle", key="-B-CIRCLE-"),
                     ts.TButton("Rectangle", key="-B-RECT-"),
                     ts.TButton("Text", key="-B-TEXT-"),
                     ts.TButton("Move figure", key="-B-MOVEF-"),
                     ts.TButton("Delete last", key="-B-DELF-"),
                     ts.TButton("Clear", key="-B-CLEARG-")]])],
        [ts.Column([[ts.TText("Shape / Canvas / Image")],
                    [ts.TShape("rectangle", size=(46, 22), fill_color="#3a7bd5"),
                     ts.TShape("oval", size=(46, 22), fill_color="#4caf50"),
                     ts.TShape("triangle", size=(40, 22), fill_color="#ff9800"),
                     ts.TShape("line", size=(40, 22), line_color="#666666"),
                     ts.VerticalSeparator(),
                     ts.TCanvas((70, 40), background_color="#e8eef7"),
                     ts.VerticalSeparator(),
                     ts.TImage(data_base64=ts.DEFAULT_BASE64_ICON)]])],
    ]


def tab_containers():
    frame = ts.TFrame("Framed group", [[ts.TInput("inside frame", key="-IN-FRAME-")]],
                      key="-FRAME-")
    splitter = ts.TSplitter(
        [[[ts.TText("Left pane")], [ts.TListbox(["A", "B", "C"], size=(9, 3))]],
         [[ts.TText("Right pane (drag the sash)")], [ts.TInput("drag me", size=(18, 1))]]],
        key="-SPLIT-")
    scroll = ts.TScrollableColumn(
        [[ts.TText(f"  scrolled row {i:>2d} ")] for i in range(1, 21)],
        size=(140, 110), key="-SCROLL-", background_color="#f7f7f7")
    flow = ts.TFlowPanel(
        [ts.TButton(f"Button {i}", size=(6, 1)) for i in range(1, 9)],
        wrap_width=640, key="-FLOW-")
    calendar = ts.TCalendar(key="-CAL-", enable_events=True)
    band_top = ts.Column([
        [ts.Column([[ts.TText("Frame")], [frame]]),
         ts.VerticalSeparator(),
         ts.Column([[ts.TText("Splitter (drag the middle sash)")], [splitter]])],
    ])
    band_mid = ts.Column([
        [ts.Column([[ts.TText("ScrollableColumn (mouse wheel)")], [scroll]]),
         ts.VerticalSeparator(),
         ts.Column([[ts.TText("Column (plain container)")],
                    [ts.TColumn([[ts.TText("Inner element one")],
                                [ts.TText("Inner element two")],
                                [ts.TButton("Button in column")]])]]),
         ts.VerticalSeparator(),
         ts.Column([[ts.TText("Calendar (embedded)")], [calendar]])],
    ])
    band_flow = ts.Column([
        [ts.TText("FlowPanel (resize the window to see wrapping)")],
        [flow],
    ])
    return [[band_top], [band_mid], [band_flow]]


def tab_fancy():
    """Canvas-drawn widgets page."""
    return [
        [ts.Column([[ts.TText("RoundButton (rounded/round buttons Tk cannot draw)")],
                    [ts.TRoundButton("Rounded", size=(110, 30), radius=14,
                                     fill_color="#e91e63", key="-RB1-"),
                     ts.TRoundButton("O", size=(40, 40), radius=20,
                                     fill_color="#4caf50", key="-RB2-"),
                     ts.TRoundButton("Dark blue", size=(110, 30), radius=8,
                                     fill_color="#3a7bd5", key="-RB3-")]])],
        [ts.Column([[ts.TText("ImageButton (whole image clicks)")],
                    [ts.TImageButton(data_base64=ts.DEFAULT_BASE64_ICON,
                                     key="-IB-"),
                     ts.TText("<- click this logo")]])],
        [ts.Column([[ts.TText("TextProgressBar (progress bar with percent text)")],
                    [ts.TTextProgressBar(100, current_value=60, size=(180, 22),
                                         bar_color="#4caf50", key="-TPB-"),
                     ts.TButton("+10", key="-B-TPB-ADD-"),
                     ts.TButton("Zero", key="-B-TPB-ZERO-")]])],
    ]


def tab_themes():
    """A visual swatch + preview for each of the five built-in themes.

    Clicking a swatch row opens a sample window in that theme; the
    ``Set as default`` button switches the global theme for every
    future window. The System row is just there as the visual baseline
    (no color overrides -- it shows whatever the OS already paints).
    """
    from TkSimpleGUI._theme_data import LOOK_AND_FEEL_TABLE

    rows = []
    rows.append([ts.TText(
        "Click a theme to open a sample window in that palette, or set it "
        "as the default for new windows. Five hand picked palettes, all "
        "low chroma, suitable for both commercial and personal apps."
    )])
    for name in ("System", "Slate", "Daylight", "Dusk", "Sage"):
        palette = LOOK_AND_FEEL_TABLE[name]["COLOR_LIST"]
        bg, accent, panel, fg = palette
        # System uses sentinel "system" placeholders -- resolve to a
        # neutral sample swatch so the row still shows something
        sample = ["#cfd2d6" if c == "system" else c for c in (bg, accent, panel, fg)]
        swatch = ts.TCanvas((180, 40), key=f"-SW-{name}-", background_color=sample[0])
        description = " / ".join(LOOK_AND_FEEL_TABLE[name].get("DESCRIPTION", []))
        row = ts.Column([
            [ts.TText(f"{name:9s}", size=(10, 1),
                      font=("Segoe UI", 10, "bold"), key=f"-LBL-{name}-"),
             swatch,
             ts.TText(description, size=(38, 1), text_color="#666666",
                      key=f"-DESC-{name}-"),
             ts.TButton("Preview", key=f"-PREVIEW-{name}-"),
             ts.TButton("Set as default", key=f"-SET-{name}-")]
        ], key=f"-ROW-{name}-", pad=(2, 2))
        rows.append([row])
    return rows


def tab_system():
    return [
        [ts.Column([[ts.TText("Popup family")],
                    [ts.TButton("Message", key="-P-MSG-"), ts.TButton("Yes/No", key="-P-YN-"),
                     ts.TButton("Error", key="-P-ERR-"),
                             ts.TButton("Scrolled text", key="-P-SCROLL-"),
                     ts.TButton("Input", key="-P-TEXT-"), ts.TButton("File", key="-P-FILE-"),
                     ts.TButton("Folder", key="-P-FOLDER-"), ts.TButton("Date", key="-P-DATE-"),
                     ts.TButton("Font", key="-P-FONT-")]])],
        [ts.Column([[ts.TText("Window control (runtime API)")],
                    [ts.TButton("Center", key="-W-CENTER-"), ts.TButton("Maximize", key="-W-MAX-"),
                     ts.TButton("Minimize", key="-W-MIN-"), ts.TButton("Restore", key="-W-NORM-"),
                     ts.TButton("Alpha 0.6", key="-W-ALPHA-"),
                             ts.TButton("Alpha 1.0", key="-W-ALPHA1-"),
                     ts.TButton("Fade out/in", key="-W-FADE-"),
                             ts.TButton("Slide out/in", key="-W-SLIDE-")]])],
        [ts.Column([[ts.TText("Toast / background task / timers")],
                    [ts.TButton("Toast", key="-W-TOAST-"),
                     ts.TButton("Background task (2s)", key="-W-WORK-"),
                     ts.TTextProgressBar(100, current_value=0, size=(20, 14),
                                         key="-PB-WORK-"),
                     ts.TButton("Timer on", key="-W-TIMER-"),
                             ts.TButton("Timer off", key="-W-TIMEROFF-"),
                     ts.TText("00:00", key="-T-ELAPSED-", size=(8, 1))]])],
        [ts.Column([[ts.TText("LED numeric display (seven-segment)")],
                    [ts.TLED(0, digits=6, color="#ff3b30", key="-LED-COUNT-"),
                     ts.VerticalSeparator(),
                     ts.TLED("00:00", digits=5, allow_colon=True,
                             color="#33cc66", key="-LED-CLOCK-"),
                     ts.VerticalSeparator(),
                     ts.TLED(-3.14, digits=6, color="#33aaff", key="-LED-NEG-")]])],
        [ts.Column([[ts.TText("System integration")],
                    [ts.TButton("Tray: create", key="-S-TRAY-"),
                            ts.TButton("Tray: notify", key="-S-NOTIFY-"),
                     ts.TButton("Tray: close", key="-S-TRAYOFF-"),
                     ts.TButton("Clipboard set", key="-S-COPY-"),
                             ts.TButton("Clipboard get", key="-S-PASTE-"),
                     ts.TButton("Save prefs", key="-S-SAVE-"),
                             ts.TButton("i18n demo", key="-S-I18N-")],
                    [ts.TText("Left/right click the tray icon; prefs persist via UserSettings.",
                             text_color="#888888")]])],
        [ts.Column([[ts.TText("Window hierarchy (parent)")],
                    [ts.TButton("Open child window", key="-W-CHILD-"),
                     ts.TText("The child is a separate window; closing the main cascades.",
                              text_color="#888888")]])],
    ]


# ---------------------------------------------------------------- window assembly --
def build_actions():
    open_action = ts.Action("Open file", key="-ACT-OPEN-", shortcut="<Control-o>")
    save_action = ts.Action("Save file", key="-ACT-SAVE-", shortcut="<Control-s>")
    clear_action = ts.Action("Clear log", key="-ACT-CLEAR-")
    about_action = ts.Action("About", key="-ACT-ABOUT-")
    return [open_action, save_action, clear_action, about_action]


def build_main_window():
    menu_def = [
        ["&File", ["Open file", "Save file", "---", "Exit"]],
        ["&Theme", ["System (native)", "Slate", "Daylight", "Dusk", "Sage"]],
        ["&Help", ["About"]],
    ]
    toolbar = ts.TToolbar([
        ("New", "-TOOL-NEW-"), ("Open file", "-ACT-OPEN-"),
        ("Save file", "-ACT-SAVE-"), "---", ("About", "-ACT-ABOUT-"),
    ])
    tabs = ts.TTabGroup(
        [[ts.TTab("Inputs", tab_inputs()), ts.TTab("Selection", tab_selection()),
          ts.TTab("Data", tab_data()), ts.TTab("Graphics", tab_graphics()),
          ts.TTab("Containers", tab_containers()), ts.TTab("Fancy", tab_fancy()),
          ts.TTab("Themes", tab_themes()),
          ts.TTab("System", tab_system())]],
        key="-TABS-", enable_events=False, expand_x=True, expand_y=True)
    log_element = ts.TOutput(size=(96, 7), key="-LOG-", expand_x=True)
    log_element.right_click_menu = ["&Log", ["Copy log", "Clear log"]]
    layout = [
        [ts.TMenu(menu_def)],
        [toolbar],
        [tabs],
        [ts.TColumn([[ts.TText("Event log (right-click to copy/clear)")], [log_element]],
                    expand_x=True)],
        [ts.TStatusBar("", key="-STATUS-", expand_x=True), ts.TSizegrip()],
    ]
    window = ts.Window(
        "TkSimpleGUI Feature Showcase",
        layout,
        finalize=True,
        resizable=True,
        margins=(8, 6),
        actions=build_actions(),
        right_click_menu=["&Window", ["Clear log", "About"]],
        on_close=_confirm_exit,
    )
    _state["window"] = window
    _post_build(window)
    return window


def _confirm_exit(window):
    """The main window's title bar X asks before quitting.

    Returning True lets the close proceed (and tear down the app loop);
    False keeps the window open. The hard-quit path stays File > Exit.
    """
    answer = ts.popup_yes_no(
        "Quit the TkSimpleGUI feature showcase?",
        title="Exit",
    )
    return answer == "Yes"


def _draw_theme_swatches(window):
    """Paint the 4-color palette into each Themes tab canvas."""
    from TkSimpleGUI._theme_data import LOOK_AND_FEEL_TABLE

    width, height = 180, 40
    slot = width // 4
    for name in ("System", "Slate", "Daylight", "Dusk", "Sage"):
        canvas = window[f"-SW-{name}-"].widget
        canvas.delete("all")
        palette = LOOK_AND_FEEL_TABLE[name]["COLOR_LIST"]
        # when the theme is "system" the palette holds the string
        # "system" placeholders; render them as neutral greys so the
        # row still looks like a coherent swatch
        sample = ["#cfd2d6" if c == "system" else c for c in palette]
        for index, color in enumerate(sample):
            x0 = index * slot
            canvas.create_rectangle(
                x0, 0, x0 + slot, height,
                fill=color, outline="#888888", width=1,
            )


def _open_theme_preview(window, theme_name):
    """Open a small sample window painted in ``theme_name``.

    Sets the active theme first so the new window picks it up, then
    reverts to whatever the main window was using so the running app
    is not affected.
    """
    previous = ts.theme()
    ts.theme(theme_name)
    layout = [
        [ts.TText(f"Preview -- {theme_name} theme", font=("Segoe UI", 10, "bold"))],
        [ts.TText("Label / TText in this theme")],
        [ts.TInput("Input field (TInput)", key="-PREV-IN-")],
        [ts.TCheckbox("Checkbox option", key="-PREV-CB-"),
         ts.TRadio("Radio A", "g", key="-PREV-R1-", default=True),
         ts.TRadio("Radio B", "g", key="-PREV-R2-")],
        [ts.TButton("Primary"), ts.TButton("Secondary"),
         ts.TButton("Cancel")],
        [ts.TProgressBar(100, current_value=42, size=(220, 14),
                         key="-PREV-PB-")],
        [ts.TStatusBar(f"Theme: {theme_name}", size=(30, 1))],
    ]
    try:
        ts.Window(f"Preview -- {theme_name}", layout,
                  finalize=True, modal=True, resizable=False)
        log(f"opened preview window in {theme_name}", color="#1565c0")
    finally:
        # revert so the rest of the app keeps the user's chosen theme
        ts.theme(previous)


def _post_build(window):
    # theme swatches on the Themes tab
    _draw_theme_swatches(window)
    # tree nodes (icons + groups + summary rows)
    tree = window["-TREE-"]
    tree.insert_group("", "grp-fruit", "Fruit group")
    tree.insert("grp-fruit", "apple", "Apple", image_data=ICON16)
    tree.insert_summary("grp-fruit", "sum-fruit", "1 item")
    tree.insert("", "standalone", "Standalone node", image_data=ICON16)
    # initial graph figures
    graph = window["-GRAPH-"]
    graph.draw_circle((25, 40), 10, fill_color="#3a7bd5")
    graph.draw_line((0, 5), (100, 5), color="#cccccc")
    graph.draw_text("coords (50, 30)", (50, 30), color="#333333")
    # status bar: launch counter (persisted via UserSettings)
    count = (_PREFS.get("launches") or 0) + 1
    _PREFS.set("launches", count)
    _refresh_status()
    # refresh the status bar clock every second
    window.every(1000, _tick_clock)
    log(f"Welcome to TkSimpleGUI {ts.__version__} -- seven tabs, zero event loop")
    log("Events dispatch to @ts.bind_event on_* functions; Ctrl+O open, Ctrl+S save",
        color="#2e7d32")


def _refresh_status():
    window = _state["window"]
    count = _PREFS.get("launches") or 0
    window["-STATUS-"].update(
        f" ready | {time.strftime('%H:%M:%S')} | launch #{count} ")


def _tick_clock():
    window = _state["window"]
    if _STOPWATCH["start"] is not None:
        elapsed = int(time.time() - _STOPWATCH["start"])
        window["-T-ELAPSED-"].update(f"{elapsed // 60:02d}:{elapsed % 60:02d}")
        window["-LED-CLOCK-"].update(f"{elapsed // 60:02d}:{elapsed % 60:02d}")
        window["-LED-COUNT-"].update(elapsed)
    _refresh_status()


# ---------------------------------------------------------------- on_* handlers --
# all registered via @ts.bind_event; signatures mix (window, values).

# inputs tab
@ts.bind_event("-IN-NUM-")
def on_num_input(window, values):
    log(f"integer input: {values['-IN-NUM-']!r}")


@ts.bind_event("-CB-SHOW-")
def on_show_password(window, values):
    window["-IN-PASS-"].set_password_char("" if values["-CB-SHOW-"] else "*")


@ts.bind_event("-SP-")
def on_spin(window, values):
    log(f"Spin: {values['-SP-']}")


@ts.bind_event("-SL-")
def on_slider(window, values):
    window["-PB-SL-"].update(current_value=values["-SL-"])


@ts.bind_event("-B-COLOR-")
def on_color_print(window, values):
    ml = window["-ML-"]
    ml.print("info: native tk.Text tag coloring", text_color="#1565c0")
    ml.print("success: everything fine", text_color="#2e7d32")
    ml.print("warning: a yellow warning", text_color="#b8860b")
    ml.print("error: a red error", text_color="#c62828")


@ts.bind_event(["-B-UNDO-"])
def on_undo(window, values):
    window["-ML-"].undo()


@ts.bind_event(["-B-REDO-"])
def on_redo(window, values):
    window["-ML-"].redo()


@ts.bind_event(["-B-CLEAR-ML-"])
def on_clear_ml(window, values):
    window["-ML-"].clear()


@ts.bind_event("-B-FIND-")
def on_find(window, values):
    position = ts.popup_find(window["-ML-"])
    log(f"find result: {position}")


@ts.bind_event("-B-REPLACE-")
def on_replace(window, values):
    count = ts.popup_replace(window["-ML-"])
    log(f"replace done, {count} sites")


@ts.bind_event("-SUBMIT-")
def on_submit(window, values):
    log(f"form submit: user={values.get('-IN-USER-')!r} num={values.get('-IN-NUM-')!r}",
        color="#2e7d32")


# selection tab
@ts.bind_event(["-CMB-", "-OPT-", "-SP2-", "-LB-", "-CBA-", "-CBB-",
                 "-CKL-", "-R1-", "-R2-", "-R3-"])
def on_selection(window, event, values):
    log(f"selection: {event} = {values.get(event)!r}")


@ts.bind_event("-B-CKALL-")
def on_checklist_all(window, values):
    window["-CKL-"].check_all()
    log(f"checklist: {window['-CKL-'].get()}")


@ts.bind_event("-B-CKNONE-")
def on_checklist_none(window, values):
    window["-CKL-"].uncheck_all()
    log(f"checklist: {window['-CKL-'].get()}")


# data tab
@ts.bind_event("-TB-")
def on_table_select(window, values):
    table = window["-TB-"]
    records = table.selected_records
    window["-T-REC-"].update(str(records[0]) if records else "")
    log(f"table selection: {table.get()} record={records[0] if records else None}")


@ts.bind_event("-B-REBIND-")
def on_rebind(window, values):
    window["-TB-"].bind([
        {"Name": "New A", "Age": 21, "City": "Beijing"},
        {"Name": "New B", "Age": 33, "City": "Guangzhou"},
    ])
    log("Table.bind rebind done (headings auto-synced)")


@ts.bind_event("-B-ADDGRP-")
def on_tree_add_group(window, values):
    _state["tree_counter"] += 1
    key = f"grp-{_state['tree_counter']}"
    window["-TREE-"].insert_group("", key, f"Group {_state['tree_counter']}")
    log(f"tree group: {key}")


@ts.bind_event("-B-ADD-")
def on_tree_add(window, values):
    _state["tree_counter"] += 1
    name = f"Node {_state['tree_counter']}"
    window["-TREE-"].insert("grp-fruit", f"n{_state['tree_counter']}",
                            name, image_data=ICON16)
    log(f"tree insert: {name}")


@ts.bind_event("-B-DEL-")
def on_tree_del(window, values):
    tree = window["-TREE-"]
    selection = tree.widget.selection()
    if selection:
        tree.widget.delete(*selection)
        log(f"tree delete: {', '.join(str(s) for s in selection)}")
    else:
        ts.popup_notify("Select a node first")


@ts.bind_event("-B-KVGET-")
def on_kv_get(window, values):
    log(f"KeyValueEditor: {window['-KV-'].get()}")


# graphics tab
@ts.bind_event("-GRAPH-")
def on_graph_click(window, values):
    graph = window["-GRAPH-"]
    log(f"canvas click, {len(graph.widget.find_all())} figures")


@ts.bind_event(["-CH-LINE-", "-CH-BAR-", "-CH-AREA-",
                "-CH-SCATTER-", "-CH-HBAR-", "-CH-PIE-"])
def on_chart_click(window, event):
    chart = window[event]
    log(f"chart {event} clicked, {len(chart.widget.find_all())} figures")


@ts.bind_event("-B-CHUPD-")
def on_chart_update(window, values):
    import random

    chart = window["-CH-LINE-"]
    chart.update_data("2025", [random.randint(20, 45) for _ in range(6)])
    log("line chart '2025' series updated")


@ts.bind_event("-B-CHADD-")
def on_chart_add(window, values):
    import random

    chart = window["-CH-BAR-"]
    name = f"Team {len(chart.series_names) + 1}"
    chart.add_series(name, [random.randint(5, 30) for _ in range(4)])
    chart.redraw()
    log(f"bar series '{name}' added ({chart.series_names})")


@ts.bind_event("-B-CHPIE-")
def on_chart_pie(window, values):
    import random

    chart = window["-CH-PIE-"]
    names = ["alpha", "beta", "gamma", "delta"]
    pairs = [(n, random.randint(5, 60)) for n in names[: random.randint(2, 4)]]
    chart.update_data("share", pairs)
    log(f"pie reseeded: {pairs}")


def _draw(kind, window):
    graph = window["-GRAPH-"]
    _state["figure_count"] += 1
    x = 10 + (_state["figure_count"] * 13) % 80
    if kind == "circle":
        figure_id = graph.draw_circle((x, 35), 6, fill_color="#e91e63")
    elif kind == "rect":
        figure_id = graph.draw_rectangle((x, 28), (x + 8, 42),
                                         fill_color="#4caf50")
    else:
        figure_id = graph.draw_text("T", (x, 15), color="#1565c0")
    _state["figure_last"] = figure_id
    log(f"drew {kind} -> figure {figure_id}")


@ts.bind_event("-B-CIRCLE-")
def on_draw_circle(window, values):
    _draw("circle", window)


@ts.bind_event("-B-RECT-")
def on_draw_rect(window, values):
    _draw("rect", window)


@ts.bind_event("-B-TEXT-")
def on_draw_text(window, values):
    _draw("text", window)


@ts.bind_event("-B-MOVEF-")
def on_move_figure(window, values):
    figure = _state["figure_last"]
    if figure is not None:
        window["-GRAPH-"].move_figure(figure, 3, 2)
        log(f"moved figure {figure}")


@ts.bind_event("-B-DELF-")
def on_delete_figure(window, values):
    figure = _state["figure_last"]
    if figure is not None:
        window["-GRAPH-"].delete_figure(figure)
        log(f"deleted figure {figure}")
        _state["figure_last"] = None


@ts.bind_event("-B-CLEARG-")
def on_clear_graph(window, values):
    window["-GRAPH-"].erase()
    _state["figure_last"] = None
    log("canvas cleared")


@ts.bind_event("-CAL-")
def on_calendar(window, values):
    log(f"calendar: {values['-CAL-']}")


# fancy tab (canvas-drawn widgets)
@ts.bind_event(["-RB1-", "-RB2-", "-RB3-"])
def on_round_button(window, event, values):
    log(f"RoundButton click: {event}")


@ts.bind_event("-IB-")
def on_image_button(window, values):
    log("ImageButton click (whole image is the hit area)")


@ts.bind_event("-B-TPB-ADD-")
def on_tpb_add(window, values):
    bar = window["-TPB-"]
    bar.update(current_value=min(bar.max_value, bar.get() + 10))
    log(f"TextProgressBar: {bar.get()}%")


@ts.bind_event("-B-TPB-ZERO-")
def on_tpb_zero(window, values):
    window["-TPB-"].update(current_value=0)
    log("TextProgressBar zeroed")


# popup family
@ts.bind_event("-P-MSG-")
def on_p_msg(window, values):
    log(f"popup returned: {ts.popup('A popup message')!r}")


@ts.bind_event("-P-YN-")
def on_p_yn(window, values):
    log(f"popup_yes_no returned: {ts.popup_yes_no('Continue?')!r}")


@ts.bind_event("-P-ERR-")
def on_p_err(window, values):
    ts.popup_error("An error (demo)")


@ts.bind_event("-P-SCROLL-")
def on_p_scroll(window, values):
    ts.popup_scrolled(
        "\n".join(f"line {i} content" for i in range(1, 21)),
        title="Scrolled text")


@ts.bind_event("-P-TEXT-")
def on_p_text(window, values):
    log(f"popup_get_text returned: {ts.popup_get_text('Type something')!r}")


@ts.bind_event("-P-FILE-")
def on_p_file(window, values):
    log(f"file chosen: {ts.popup_get_file('Pick a file')!r}")


@ts.bind_event("-P-FOLDER-")
def on_p_folder(window, values):
    log(f"folder chosen: {ts.popup_get_folder('Pick a folder')!r}")


@ts.bind_event("-P-DATE-")
def on_p_date(window, values):
    log(f"date chosen: {ts.popup_get_date()}")


@ts.bind_event("-P-FONT-")
def on_p_font(window, values):
    log(f"font chosen: {ts.popup_get_font(include_bold_italic=True)}")


# window control
@ts.bind_event("-W-CENTER-")
def on_w_center(window, values):
    window.move_to_center()


@ts.bind_event("-W-MAX-")
def on_w_max(window, values):
    window.maximize()


@ts.bind_event("-W-MIN-")
def on_w_min(window, values):
    window.minimize()


@ts.bind_event("-W-NORM-")
def on_w_norm(window, values):
    window.normal()


@ts.bind_event("-W-ALPHA-")
def on_w_alpha(window, values):
    window.set_alpha_channel(0.5)


@ts.bind_event("-W-ALPHA1-")
def on_w_alpha1(window, values):
    window.set_alpha_channel(1.0)


@ts.bind_event("-W-FADE-")
def on_w_fade(window, values):
    ts.fade_out(window, duration_ms=400, steps=8,
                on_done=lambda: window.after(
                    150, lambda: ts.fade_in(window, duration_ms=400, steps=8)))
    log("fade out -> fade in (after chain)")


@ts.bind_event("-W-SLIDE-")
def on_w_slide(window, values):
    start = window.current_location()
    ts.slide(window, (start[0] + 120, start[1]), duration_ms=400, steps=8,
             on_done=lambda: ts.slide(window, start, duration_ms=400, steps=8))


@ts.bind_event("-W-TOAST-")
def on_w_toast(window, values):
    window.toast("Saved", title="Toast", duration_ms=2500)
    log("toast shown (bottom-right fade)")


@ts.bind_event("-W-WORK-")
def on_w_work(window, values):
    ts.animate_progress(window, "-PB-WORK-", 100,
                        duration_ms=1800, steps=18,
                        on_done=lambda: window["-PB-WORK-"].update(current_value=0))
    window.perform_long_operation(
        lambda: (time.sleep(2), "background task done")[1], end_key="-WORK-DONE-")
    log("background thread started (UI stays responsive)")


@ts.bind_event("-WORK-DONE-")
def on_work_done(window, values):
    log("perform_long_operation returned -WORK-DONE-", color="#2e7d32")


@ts.bind_event("-W-TIMER-")
def on_timer_on(window, values):
    _STOPWATCH["start"] = time.time()
    log("timer started")


@ts.bind_event("-W-TIMEROFF-")
def on_timer_off(window, values):
    _STOPWATCH["start"] = None
    window["-T-ELAPSED-"].update("00:00")
    log("timer stopped")


# hierarchy: a child window (parent=) with an event button inside
@ts.bind_event("-W-CHILD-")
def on_w_child(window, values):
    if _state["about_window"] is not None and not _state["about_window"].was_closed:
        _state["about_window"].bring_to_front()
        return
    child_layout = [
        [ts.TText("This is a child window (parent=main)")],
        [ts.TText("hierarchy: child.parent == main, main.children contains this")],
        [ts.TButton("Click me in the child", key="-CHILD-PING-")],
        [ts.TButton("Close child", key="-CHILD-CLOSE-")],
    ]
    _state["about_window"] = ts.Window(
        "Child window", child_layout, finalize=True, parent=window)
    log("child window open (cascades when the main closes)", color="#2e7d32")


@ts.bind_event("-CHILD-PING-")
def on_child_ping(window, values):
    # window is the event owner -- may be the child or the main
    log(f"child button click (from {window.title})")


@ts.bind_event("-CHILD-CLOSE-")
def on_child_close(window, values):
    if _state["about_window"] is not None:
        _state["about_window"].close()
        _state["about_window"] = None
    log("child window closed")


# system integration
@ts.bind_event("-S-TRAY-")
def on_tray_create(window, values):
    if _TRAY["obj"] is not None:
        ts.popup_notify("Tray already exists")
        return
    try:
        _TRAY["obj"] = ts.SystemTray(title="TkSimpleGUI demo",
                                     menu=["Show notification", "Exit tray"])
        log("tray icon created (left/right click it)", color="#2e7d32")
    except RuntimeError as error:
        ts.popup_error(str(error))


@ts.bind_event("-S-NOTIFY-")
def on_tray_notify(window, values):
    if _TRAY["obj"] is not None:
        _TRAY["obj"].ShowMessage("TkSimpleGUI", "A tray balloon notification")
    else:
        ts.popup_notify("Create the tray first")


@ts.bind_event("-S-TRAYOFF-")
def on_tray_off(window, values):
    if _TRAY["obj"] is not None:
        _TRAY["obj"].close()
        _TRAY["obj"] = None
        log("tray closed")


@ts.bind_event("-S-COPY-")
def on_copy(window, values):
    window.clipboard_set(f"TkSimpleGUI clipboard demo {time.time()}")
    log("clipboard written")


@ts.bind_event("-S-PASTE-")
def on_paste(window, values):
    log(f"clipboard: {window.clipboard_get()!r}")


@ts.bind_event("-S-SAVE-")
def on_save_state(window, values):
    _PREFS.set("last_theme", ts.theme())
    _PREFS.set("last_seen", time.strftime("%Y-%m-%d %H:%M:%S"))
    log(f"UserSettings saved: last_theme={_PREFS.get('last_theme')!r}, "
        f"last_seen={_PREFS.get('last_seen')}")


@ts.bind_event("-S-I18N-")
def on_i18n(window, values):
    ts.set_translations({"Open": "Ouvert", "Save": "Sauve"})
    sample = [ts._("Open"), ts._("Save"), ts._("Unknown stays")]
    log(f"i18n: {' / '.join(sample)}")
    ts.clear_translations()


# menu / toolbar / right-click shared actions
@ts.bind_event("-ACT-OPEN-")
def on_open(window, values):
    path = ts.popup_get_file("Open (Ctrl+O)")
    log(f"Action open file: {path!r}")


@ts.bind_event("-ACT-SAVE-")
def on_save(window, values):
    path = ts.popup_get_file("Save (Ctrl+S)", save_as=True)
    log(f"Action save file: {path!r}")


@ts.bind_event("-ACT-CLEAR-")
def on_clear_log(window, values):
    window["-LOG-"].clear()
    log("log cleared")


@ts.bind_event("-ACT-ABOUT-")
def on_about(window, values):
    ts.popup_ok(
        f"TkSimpleGUI {ts.__version__}\n\nOO rewrite forked from PySimpleGUI 4.x\n"
        "zero dependencies / Python 3.7+ / native default look",
        title="About")


@ts.bind_event("Copy log")
def on_copy_log(window, values):
    window.clipboard_set(window["-LOG-"].get())
    ts.popup_notify("Log copied to clipboard")


@ts.bind_event(["System (native)", "Slate", "Daylight", "Dusk", "Sage"])
def on_theme(window, event, values):
    name = ts.theme("System" if event == "System (native)" else event)
    log(f"theme switched to {name} (applies to new windows)", color="#1565c0")


# Themes tab: per-row Preview / Set as default buttons.
_THEME_NAMES = ("System", "Slate", "Daylight", "Dusk", "Sage")


@ts.bind_event([f"-PREVIEW-{n}-" for n in _THEME_NAMES])
def on_theme_preview(window, event, values):
    name = event.replace("-PREVIEW-", "").rstrip("-")
    _open_theme_preview(window, name)


@ts.bind_event([f"-SET-{n}-" for n in _THEME_NAMES])
def on_theme_set_default(window, event, values):
    name = event.replace("-SET-", "").rstrip("-")
    applied = ts.theme(name)
    log(f"default theme set to {applied} (next window will use it)",
        color="#2e7d32")


@ts.bind_event("-TOOL-NEW-")
def on_tool_new(window, values):
    log("toolbar: New")


@ts.bind_event("Exit")
def on_exit(window, values):
    if _TRAY["obj"] is not None:
        _TRAY["obj"].close()
        _TRAY["obj"] = None
    ts.Window.close_all()


# ---------------------------------------------------------------- entry --
def main(argv=None):
    ts.set_dpi_awareness()  # crisp rendering on Windows high-DPI (once per process)
    smoke = "--smoke" in (argv or sys.argv[1:])
    window = build_main_window()
    try:
        if smoke:
            # smoke: call a few handlers directly to verify wiring (no popups)
            window.read(timeout=200)
            on_color_print(window, {})
            on_slider(window, {"-SL-": 80})
            on_w_toast(window, {})
            deadline = time.time() + 1.5
            while time.time() < deadline:
                window.read(timeout=100)
            window.close()
            print("SMOKE OK")
            return 0
        # zero user loop: window.run() starts the app (on_* handlers are on default_app)
        window.run()
    finally:
        if _TRAY["obj"] is not None:
            _TRAY["obj"].close()
        ts.Window.close_all()
    return 0


if __name__ == "__main__":
    main()
