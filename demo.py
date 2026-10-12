#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TkSimpleGUI full-featured showcase (current standard style).

Demonstrates the **recommended style**:
- ``window.run()`` -- the root object starts the app, zero user loop
- ``@sg.bind_event`` + ``on_*`` functions -- dispatched by the built-in
  default event manager (no explicit imports)
- ``Action`` -- actions shared between menus, toolbars and shortcuts
- ``parent=`` -- window hierarchy (child window demo, cascading close)
- T-prefix naming, Toast, RoundButton, TextProgressBar, slider bubbles...

Run::

    python demo.py            # interactive mode
    python demo.py --smoke    # self-test: pump events ~2s, then exit
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
import TkSimpleGUI as sg  # noqa: E402

# 16x16 badge (table row icons / tree node icons)
ICON16 = (
    b"iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAiUlEQVR42mNgQANuPQ//48MM"
    b"uIBz283/pGAUzQ6NF/+Tg+EG2Nac+k8OBmu2Kjv0nxLMYF646z8lmMEkZ/N/SjCDYdrq/5Rg"
    b"Br3Exf8pwQzaMXP+U4IZNMKm/KcEM6gG9vynBIPTgpJP639yMDwlyrvV/icHo+QHGcfS/6Rg"
    b"nLlSyibvPz6Mrh4AeY7yRAY4AssAAAAASUVORK5CYII="
)

_STOPWATCH = {"start": None}
_TRAY = {"obj": None}
_PREFS = sg.UserSettings("demo.json")

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
    band_top = sg.Column([
        [sg.Column([[sg.TText("Integer validation (digits only)")],
                    [sg.TInput("", key="-IN-NUM-", size=(12, 1), validate="key",
                              validate_command=sg.validate_integer,
                              enable_events=True)]]),
         sg.Column([[sg.TText("Password")],
                    [sg.TInput("", key="-IN-PASS-", size=(12, 1), password_char="*")],
                    [sg.TCheckbox("Show password", key="-CB-SHOW-", enable_events=True)]]),
         sg.Column([[sg.TLabeledEdit("Username", "yunluo", key="-IN-USER-")],
                    [sg.TButton("Submit form", key="-SUBMIT-")]]),
         sg.Column([[sg.TText("Spin")],
                    [sg.TSpin([str(n) for n in range(1, 11)], initial_value="5",
                              key="-SP-", enable_events=True)]])],
    ])
    band_slider = sg.Column([
        [sg.TText("Slider drives the progress bar (show_value bubble while dragging):")],
        [sg.TSlider((0, 100), default_value=30, key="-SL-",
                    enable_events=True, size=(18, 15), show_value=True),
         sg.TProgressBar(100, current_value=30, size=(20, 12), key="-PB-SL-")],
    ])
    band_multiline = sg.Column([
        [sg.TMultiline("Multiline area (undo/redo, colored output, find/replace)\n",
                       key="-ML-", size=(56, 5))],
        [sg.TButton("Color output", key="-B-COLOR-"), sg.TButton("Undo", key="-B-UNDO-"),
         sg.TButton("Redo", key="-B-REDO-"), sg.TButton("Find", key="-B-FIND-"),
         sg.TButton("Replace", key="-B-REPLACE-"), sg.TButton("Clear", key="-B-CLEAR-ML-")],
    ])
    return [[band_top], [band_slider], [band_multiline]]


def tab_selection():
    band = sg.Column([
        [sg.Column([[sg.TText("Combo")],
                    [sg.TCombo(["Red", "Green", "Blue"], default_value="Red",
                              key="-CMB-", enable_events=True)],
                    [sg.TText("OptionMenu")],
                    [sg.TOptionMenu(["First", "Second", "Third"], key="-OPT-",
                                   enable_events=True)],
                    [sg.TText("Spin")],
                    [sg.TSpin(["Low", "Medium", "High"], initial_value="Medium",
                             key="-SP2-", enable_events=True)]],
                   ),
         sg.Column([[sg.TText("Listbox (multi-select)")],
                    [sg.TListbox(["Item one", "Item two", "Item three", "Item four"],
                                size=(14, 4), select_mode=sg.SelectMode.EXTENDED,
                                key="-LB-", enable_events=True)]]),
         sg.Column([[sg.TText("Checkbox")],
                    [sg.TCheckbox("Check A", key="-CBA-", enable_events=True)],
                    [sg.TCheckbox("Check B", key="-CBB-", enable_events=True)]]),
         sg.Column([[sg.TText("CheckList")],
                    [sg.TCheckList(["Melon", "Apple", "Banana"],
                                  default_checked=["Apple"], key="-CKL-",
                                  enable_events=True)],
                    [sg.TButton("All", key="-B-CKALL-"),
                     sg.TButton("None", key="-B-CKNONE-")]]),
         sg.Column([[sg.TText("Radio (exclusive)")],
                    [sg.TRadio("Plan 1", "plan", default=True, key="-R1-",
                              enable_events=True)],
                    [sg.TRadio("Plan 2", "plan", key="-R2-", enable_events=True)],
                    [sg.TRadio("Plan 3", "plan", key="-R3-", enable_events=True)]])],
    ])
    return [[band]]


def tab_data():
    records = [
        {"Name": "Yunluo", "Age": 30, "City": "Shenzhen"},
        {"Name": "Ming", "Age": 24, "City": "Hangzhou"},
        {"Name": "Qiang", "Age": 36, "City": "Chengdu"},
        {"Name": "Mei", "Age": 28, "City": "Shanghai"},
    ]
    table = sg.TTable([], headings=[], key="-TB-", enable_edit=True,
                      row_icons=[ICON16, ICON16, ICON16, ICON16], num_rows=5,
                      auto_size_columns=False, col_widths=[10, 8, 10])
    table.bind(records)
    tree = sg.TTree(headings=["Node"], show_headings=False, num_rows=6, key="-TREE-")
    kv = sg.TKeyValueEditor([("Host", "localhost"), ("Port", "5432")], key="-KV-")
    band = sg.Column([
        [sg.Column([[sg.TText("Table: click header sorts / double-click edits / row icons / drag separator")],
                    [table],
                    [sg.TButton("Rebind data", key="-B-REBIND-"),
                     sg.TText("Selected record:"),
                     sg.TText("", key="-T-REC-", size=(22, 1))]]),
         sg.Column([[sg.TText("Tree (icons / groups / summary rows)")],
                    [tree],
                    [sg.TButton("Add group", key="-B-ADDGRP-"),
                     sg.TButton("Add node", key="-B-ADD-"),
                     sg.TButton("Delete node", key="-B-DEL-")]]),
         sg.Column([[sg.TText("KeyValue editor (TValEdit)")],
                    [kv],
                    [sg.TButton("Read values", key="-B-KVGET-")]])],
    ])
    return [[band]]


def tab_graphics():
    graph = sg.TGraph((320, 160), (0, 0), (100, 54), key="-GRAPH-",
                      enable_events=True, background_color="#ffffff")
    return [
        [sg.Column([[sg.TText("TGraph (user coords + figure handles) -- click the canvas")],
                    [graph],
                    [sg.TButton("Circle", key="-B-CIRCLE-"),
                     sg.TButton("Rectangle", key="-B-RECT-"),
                     sg.TButton("Text", key="-B-TEXT-"),
                     sg.TButton("Move figure", key="-B-MOVEF-"),
                     sg.TButton("Delete last", key="-B-DELF-"),
                     sg.TButton("Clear", key="-B-CLEARG-")]])],
        [sg.Column([[sg.TText("Shape / Canvas / Image")],
                    [sg.TShape("rectangle", size=(46, 22), fill_color="#3a7bd5"),
                     sg.TShape("oval", size=(46, 22), fill_color="#4caf50"),
                     sg.TShape("triangle", size=(40, 22), fill_color="#ff9800"),
                     sg.TShape("line", size=(40, 22), line_color="#666666"),
                     sg.VerticalSeparator(),
                     sg.TCanvas((70, 40), background_color="#e8eef7"),
                     sg.VerticalSeparator(),
                     sg.TImage(data_base64=sg.DEFAULT_BASE64_ICON)]])],
    ]


def tab_containers():
    frame = sg.TFrame("Framed group", [[sg.TInput("inside frame", key="-IN-FRAME-")]],
                      key="-FRAME-")
    splitter = sg.TSplitter(
        [[[sg.TText("Left pane")], [sg.TListbox(["A", "B", "C"], size=(9, 3))]],
         [[sg.TText("Right pane (drag the sash)")], [sg.TInput("drag me", size=(18, 1))]]],
        key="-SPLIT-")
    scroll = sg.TScrollableColumn(
        [[sg.TText(f"  scrolled row {i:>2d} ")] for i in range(1, 21)],
        size=(140, 110), key="-SCROLL-", background_color="#f7f7f7")
    flow = sg.TFlowPanel(
        [sg.TButton(f"Button {i}", size=(6, 1)) for i in range(1, 9)],
        wrap_width=640, key="-FLOW-")
    calendar = sg.TCalendar(key="-CAL-", enable_events=True)
    band_top = sg.Column([
        [sg.Column([[sg.TText("Frame")], [frame]]),
         sg.VerticalSeparator(),
         sg.Column([[sg.TText("Splitter (drag the middle sash)")], [splitter]])],
    ])
    band_mid = sg.Column([
        [sg.Column([[sg.TText("ScrollableColumn (mouse wheel)")], [scroll]]),
         sg.VerticalSeparator(),
         sg.Column([[sg.TText("Column (plain container)")],
                    [sg.TColumn([[sg.TText("Inner element one")],
                                [sg.TText("Inner element two")],
                                [sg.TButton("Button in column")]])]]),
         sg.VerticalSeparator(),
         sg.Column([[sg.TText("Calendar (embedded)")], [calendar]])],
    ])
    band_flow = sg.Column([
        [sg.TText("FlowPanel (resize the window to see wrapping)")],
        [flow],
    ])
    return [[band_top], [band_mid], [band_flow]]


def tab_fancy():
    """Canvas-drawn widgets page."""
    return [
        [sg.Column([[sg.TText("RoundButton (rounded/round buttons Tk cannot draw)")],
                    [sg.TRoundButton("Rounded", size=(110, 30), radius=14,
                                     fill_color="#e91e63", key="-RB1-"),
                     sg.TRoundButton("O", size=(40, 40), radius=20,
                                     fill_color="#4caf50", key="-RB2-"),
                     sg.TRoundButton("Dark blue", size=(110, 30), radius=8,
                                     fill_color="#3a7bd5", key="-RB3-")]])],
        [sg.Column([[sg.TText("ImageButton (whole image clicks)")],
                    [sg.TImageButton(data_base64=sg.DEFAULT_BASE64_ICON,
                                     key="-IB-"),
                     sg.TText("<- click this logo")]])],
        [sg.Column([[sg.TText("TextProgressBar (progress bar with percent text)")],
                    [sg.TTextProgressBar(100, current_value=60, size=(180, 22),
                                         bar_color="#4caf50", key="-TPB-"),
                     sg.TButton("+10", key="-B-TPB-ADD-"),
                     sg.TButton("Zero", key="-B-TPB-ZERO-")]])],
    ]


def tab_system():
    return [
        [sg.Column([[sg.TText("Popup family")],
                    [sg.TButton("Message", key="-P-MSG-"), sg.TButton("Yes/No", key="-P-YN-"),
                     sg.TButton("Error", key="-P-ERR-"), sg.TButton("Scrolled text", key="-P-SCROLL-"),
                     sg.TButton("Input", key="-P-TEXT-"), sg.TButton("File", key="-P-FILE-"),
                     sg.TButton("Folder", key="-P-FOLDER-"), sg.TButton("Date", key="-P-DATE-"),
                     sg.TButton("Font", key="-P-FONT-")]])],
        [sg.Column([[sg.TText("Window control (runtime API)")],
                    [sg.TButton("Center", key="-W-CENTER-"), sg.TButton("Maximize", key="-W-MAX-"),
                     sg.TButton("Minimize", key="-W-MIN-"), sg.TButton("Restore", key="-W-NORM-"),
                     sg.TButton("Alpha 0.6", key="-W-ALPHA-"), sg.TButton("Alpha 1.0", key="-W-ALPHA1-"),
                     sg.TButton("Fade out/in", key="-W-FADE-"), sg.TButton("Slide out/in", key="-W-SLIDE-")]])],
        [sg.Column([[sg.TText("Toast / background task / timers")],
                    [sg.TButton("Toast", key="-W-TOAST-"),
                     sg.TButton("Background task (2s)", key="-W-WORK-"),
                     sg.TTextProgressBar(100, current_value=0, size=(20, 14),
                                         key="-PB-WORK-"),
                     sg.TButton("Timer on", key="-W-TIMER-"), sg.TButton("Timer off", key="-W-TIMEROFF-"),
                     sg.TText("00:00", key="-T-ELAPSED-", size=(8, 1))]])],
        [sg.Column([[sg.TText("System integration")],
                    [sg.TButton("Tray: create", key="-S-TRAY-"), sg.TButton("Tray: notify", key="-S-NOTIFY-"),
                     sg.TButton("Tray: close", key="-S-TRAYOFF-"),
                     sg.TButton("Clipboard set", key="-S-COPY-"), sg.TButton("Clipboard get", key="-S-PASTE-"),
                     sg.TButton("Save prefs", key="-S-SAVE-"), sg.TButton("i18n demo", key="-S-I18N-")],
                    [sg.TText("Left/right click the tray icon; prefs persist via UserSettings.",
                             text_color="#888888")]])],
        [sg.Column([[sg.TText("Window hierarchy (parent)")],
                    [sg.TButton("Open child window", key="-W-CHILD-"),
                     sg.TText("The child is a separate window; closing the main cascades.",
                              text_color="#888888")]])],
    ]


# ---------------------------------------------------------------- window assembly --
def build_actions():
    open_action = sg.Action("Open file", key="-ACT-OPEN-", shortcut="<Control-o>")
    save_action = sg.Action("Save file", key="-ACT-SAVE-", shortcut="<Control-s>")
    clear_action = sg.Action("Clear log", key="-ACT-CLEAR-")
    about_action = sg.Action("About", key="-ACT-ABOUT-")
    return [open_action, save_action, clear_action, about_action]


def build_main_window():
    menu_def = [
        ["&File", ["Open file", "Save file", "---", "Exit"]],
        ["&Theme", ["Native look", "DarkBlue3 theme"]],
        ["&Help", ["About"]],
    ]
    toolbar = sg.TToolbar([
        ("New", "-TOOL-NEW-"), ("Open file", "-ACT-OPEN-"),
        ("Save file", "-ACT-SAVE-"), "---", ("About", "-ACT-ABOUT-"),
    ])
    tabs = sg.TTabGroup(
        [[sg.TTab("Inputs", tab_inputs()), sg.TTab("Selection", tab_selection()),
          sg.TTab("Data", tab_data()), sg.TTab("Graphics", tab_graphics()),
          sg.TTab("Containers", tab_containers()), sg.TTab("Fancy", tab_fancy()),
          sg.TTab("System", tab_system())]],
        key="-TABS-", enable_events=False, expand_x=True, expand_y=True)
    log_element = sg.TOutput(size=(96, 7), key="-LOG-", expand_x=True)
    log_element.right_click_menu = ["&Log", ["Copy log", "Clear log"]]
    layout = [
        [sg.TMenu(menu_def)],
        [toolbar],
        [tabs],
        [sg.TColumn([[sg.TText("Event log (right-click to copy/clear)")], [log_element]],
                    expand_x=True)],
        [sg.TStatusBar("", key="-STATUS-", expand_x=True), sg.TSizegrip()],
    ]
    window = sg.Window(
        "TkSimpleGUI Feature Showcase",
        layout,
        finalize=True,
        resizable=True,
        margins=(8, 6),
        actions=build_actions(),
        right_click_menu=["&Window", ["Clear log", "About"]],
    )
    _state["window"] = window
    _post_build(window)
    return window


def _post_build(window):
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
    log(f"Welcome to TkSimpleGUI {sg.__version__} -- seven tabs, zero event loop")
    log("Events dispatch to @sg.bind_event on_* functions; Ctrl+O open, Ctrl+S save",
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
    _refresh_status()


# ---------------------------------------------------------------- on_* handlers --
# all registered via @sg.bind_event; signatures mix (window, values).

# inputs tab
@sg.bind_event("-IN-NUM-")
def on_num_input(window, values):
    log(f"integer input: {values['-IN-NUM-']!r}")


@sg.bind_event("-CB-SHOW-")
def on_show_password(window, values):
    window["-IN-PASS-"].set_password_char("" if values["-CB-SHOW-"] else "*")


@sg.bind_event("-SP-")
def on_spin(window, values):
    log(f"Spin: {values['-SP-']}")


@sg.bind_event("-SL-")
def on_slider(window, values):
    window["-PB-SL-"].update(current_value=values["-SL-"])


@sg.bind_event("-B-COLOR-")
def on_color_print(window, values):
    ml = window["-ML-"]
    ml.print("info: native tk.Text tag coloring", text_color="#1565c0")
    ml.print("success: everything fine", text_color="#2e7d32")
    ml.print("warning: a yellow warning", text_color="#b8860b")
    ml.print("error: a red error", text_color="#c62828")


@sg.bind_event(["-B-UNDO-"])
def on_undo(window, values):
    window["-ML-"].undo()


@sg.bind_event(["-B-REDO-"])
def on_redo(window, values):
    window["-ML-"].redo()


@sg.bind_event(["-B-CLEAR-ML-"])
def on_clear_ml(window, values):
    window["-ML-"].clear()


@sg.bind_event("-B-FIND-")
def on_find(window, values):
    position = sg.popup_find(window["-ML-"])
    log(f"find result: {position}")


@sg.bind_event("-B-REPLACE-")
def on_replace(window, values):
    count = sg.popup_replace(window["-ML-"])
    log(f"replace done, {count} sites")


@sg.bind_event("-SUBMIT-")
def on_submit(window, values):
    log(f"form submit: user={values.get('-IN-USER-')!r} num={values.get('-IN-NUM-')!r}",
        color="#2e7d32")


# selection tab
@sg.bind_event(["-CMB-", "-OPT-", "-SP2-", "-LB-", "-CBA-", "-CBB-",
                 "-CKL-", "-R1-", "-R2-", "-R3-"])
def on_selection(window, event, values):
    log(f"selection: {event} = {values.get(event)!r}")


@sg.bind_event("-B-CKALL-")
def on_checklist_all(window, values):
    window["-CKL-"].check_all()
    log(f"checklist: {window['-CKL-'].get()}")


@sg.bind_event("-B-CKNONE-")
def on_checklist_none(window, values):
    window["-CKL-"].uncheck_all()
    log(f"checklist: {window['-CKL-'].get()}")


# data tab
@sg.bind_event("-TB-")
def on_table_select(window, values):
    table = window["-TB-"]
    records = table.selected_records
    window["-T-REC-"].update(str(records[0]) if records else "")
    log(f"table selection: {table.get()} record={records[0] if records else None}")


@sg.bind_event("-B-REBIND-")
def on_rebind(window, values):
    window["-TB-"].bind([
        {"Name": "New A", "Age": 21, "City": "Beijing"},
        {"Name": "New B", "Age": 33, "City": "Guangzhou"},
    ])
    log("Table.bind rebind done (headings auto-synced)")


@sg.bind_event("-B-ADDGRP-")
def on_tree_add_group(window, values):
    _state["tree_counter"] += 1
    key = f"grp-{_state['tree_counter']}"
    window["-TREE-"].insert_group("", key, f"Group {_state['tree_counter']}")
    log(f"tree group: {key}")


@sg.bind_event("-B-ADD-")
def on_tree_add(window, values):
    _state["tree_counter"] += 1
    name = f"Node {_state['tree_counter']}"
    window["-TREE-"].insert("grp-fruit", f"n{_state['tree_counter']}",
                            name, image_data=ICON16)
    log(f"tree insert: {name}")


@sg.bind_event("-B-DEL-")
def on_tree_del(window, values):
    tree = window["-TREE-"]
    selection = tree.widget.selection()
    if selection:
        tree.widget.delete(*selection)
        log(f"tree delete: {', '.join(str(s) for s in selection)}")
    else:
        sg.popup_notify("Select a node first")


@sg.bind_event("-B-KVGET-")
def on_kv_get(window, values):
    log(f"KeyValueEditor: {window['-KV-'].get()}")


# graphics tab
@sg.bind_event("-GRAPH-")
def on_graph_click(window, values):
    graph = window["-GRAPH-"]
    log(f"canvas click, {len(graph.widget.find_all())} figures")


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


@sg.bind_event("-B-CIRCLE-")
def on_draw_circle(window, values):
    _draw("circle", window)


@sg.bind_event("-B-RECT-")
def on_draw_rect(window, values):
    _draw("rect", window)


@sg.bind_event("-B-TEXT-")
def on_draw_text(window, values):
    _draw("text", window)


@sg.bind_event("-B-MOVEF-")
def on_move_figure(window, values):
    figure = _state["figure_last"]
    if figure is not None:
        window["-GRAPH-"].move_figure(figure, 3, 2)
        log(f"moved figure {figure}")


@sg.bind_event("-B-DELF-")
def on_delete_figure(window, values):
    figure = _state["figure_last"]
    if figure is not None:
        window["-GRAPH-"].delete_figure(figure)
        log(f"deleted figure {figure}")
        _state["figure_last"] = None


@sg.bind_event("-B-CLEARG-")
def on_clear_graph(window, values):
    window["-GRAPH-"].erase()
    _state["figure_last"] = None
    log("canvas cleared")


@sg.bind_event("-CAL-")
def on_calendar(window, values):
    log(f"calendar: {values['-CAL-']}")


# fancy tab (canvas-drawn widgets)
@sg.bind_event(["-RB1-", "-RB2-", "-RB3-"])
def on_round_button(window, event, values):
    log(f"RoundButton click: {event}")


@sg.bind_event("-IB-")
def on_image_button(window, values):
    log("ImageButton click (whole image is the hit area)")


@sg.bind_event("-B-TPB-ADD-")
def on_tpb_add(window, values):
    bar = window["-TPB-"]
    bar.update(current_value=min(bar.max_value, bar.get() + 10))
    log(f"TextProgressBar: {bar.get()}%")


@sg.bind_event("-B-TPB-ZERO-")
def on_tpb_zero(window, values):
    window["-TPB-"].update(current_value=0)
    log("TextProgressBar zeroed")


# popup family
@sg.bind_event("-P-MSG-")
def on_p_msg(window, values):
    log(f"popup returned: {sg.popup('A popup message')!r}")


@sg.bind_event("-P-YN-")
def on_p_yn(window, values):
    log(f"popup_yes_no returned: {sg.popup_yes_no('Continue?')!r}")


@sg.bind_event("-P-ERR-")
def on_p_err(window, values):
    sg.popup_error("An error (demo)")


@sg.bind_event("-P-SCROLL-")
def on_p_scroll(window, values):
    sg.popup_scrolled(
        "\n".join(f"line {i} content" for i in range(1, 21)),
        title="Scrolled text")


@sg.bind_event("-P-TEXT-")
def on_p_text(window, values):
    log(f"popup_get_text returned: {sg.popup_get_text('Type something')!r}")


@sg.bind_event("-P-FILE-")
def on_p_file(window, values):
    log(f"file chosen: {sg.popup_get_file('Pick a file')!r}")


@sg.bind_event("-P-FOLDER-")
def on_p_folder(window, values):
    log(f"folder chosen: {sg.popup_get_folder('Pick a folder')!r}")


@sg.bind_event("-P-DATE-")
def on_p_date(window, values):
    log(f"date chosen: {sg.popup_get_date()}")


@sg.bind_event("-P-FONT-")
def on_p_font(window, values):
    log(f"font chosen: {sg.popup_get_font(include_bold_italic=True)}")


# window control
@sg.bind_event("-W-CENTER-")
def on_w_center(window, values):
    window.move_to_center()


@sg.bind_event("-W-MAX-")
def on_w_max(window, values):
    window.maximize()


@sg.bind_event("-W-MIN-")
def on_w_min(window, values):
    window.minimize()


@sg.bind_event("-W-NORM-")
def on_w_norm(window, values):
    window.normal()


@sg.bind_event("-W-ALPHA-")
def on_w_alpha(window, values):
    window.set_alpha_channel(0.5)


@sg.bind_event("-W-ALPHA1-")
def on_w_alpha1(window, values):
    window.set_alpha_channel(1.0)


@sg.bind_event("-W-FADE-")
def on_w_fade(window, values):
    sg.fade_out(window, duration_ms=400, steps=8,
                on_done=lambda: window.after(
                    150, lambda: sg.fade_in(window, duration_ms=400, steps=8)))
    log("fade out -> fade in (after chain)")


@sg.bind_event("-W-SLIDE-")
def on_w_slide(window, values):
    start = window.current_location()
    sg.slide(window, (start[0] + 120, start[1]), duration_ms=400, steps=8,
             on_done=lambda: sg.slide(window, start, duration_ms=400, steps=8))


@sg.bind_event("-W-TOAST-")
def on_w_toast(window, values):
    window.toast("Saved", title="Toast", duration_ms=2500)
    log("toast shown (bottom-right fade)")


@sg.bind_event("-W-WORK-")
def on_w_work(window, values):
    sg.animate_progress(window, "-PB-WORK-", 100,
                        duration_ms=1800, steps=18,
                        on_done=lambda: window["-PB-WORK-"].update(current_value=0))
    window.perform_long_operation(
        lambda: (time.sleep(2), "background task done")[1], end_key="-WORK-DONE-")
    log("background thread started (UI stays responsive)")


@sg.bind_event("-WORK-DONE-")
def on_work_done(window, values):
    log("perform_long_operation returned -WORK-DONE-", color="#2e7d32")


@sg.bind_event("-W-TIMER-")
def on_timer_on(window, values):
    _STOPWATCH["start"] = time.time()
    log("timer started")


@sg.bind_event("-W-TIMEROFF-")
def on_timer_off(window, values):
    _STOPWATCH["start"] = None
    window["-T-ELAPSED-"].update("00:00")
    log("timer stopped")


# hierarchy: a child window (parent=) with an event button inside
@sg.bind_event("-W-CHILD-")
def on_w_child(window, values):
    if _state["about_window"] is not None and not _state["about_window"].was_closed:
        _state["about_window"].bring_to_front()
        return
    child_layout = [
        [sg.TText("This is a child window (parent=main)")],
        [sg.TText("hierarchy: child.parent == main, main.children contains this")],
        [sg.TButton("Click me in the child", key="-CHILD-PING-")],
        [sg.TButton("Close child", key="-CHILD-CLOSE-")],
    ]
    _state["about_window"] = sg.Window(
        "Child window", child_layout, finalize=True, parent=window)
    log("child window open (cascades when the main closes)", color="#2e7d32")


@sg.bind_event("-CHILD-PING-")
def on_child_ping(window, values):
    # window is the event owner -- may be the child or the main
    log(f"child button click (from {window.title})")


@sg.bind_event("-CHILD-CLOSE-")
def on_child_close(window, values):
    if _state["about_window"] is not None:
        _state["about_window"].close()
        _state["about_window"] = None
    log("child window closed")


# system integration
@sg.bind_event("-S-TRAY-")
def on_tray_create(window, values):
    if _TRAY["obj"] is not None:
        sg.popup_notify("Tray already exists")
        return
    try:
        _TRAY["obj"] = sg.SystemTray(title="TkSimpleGUI demo",
                                     menu=["Show notification", "Exit tray"])
        log("tray icon created (left/right click it)", color="#2e7d32")
    except RuntimeError as error:
        sg.popup_error(str(error))


@sg.bind_event("-S-NOTIFY-")
def on_tray_notify(window, values):
    if _TRAY["obj"] is not None:
        _TRAY["obj"].ShowMessage("TkSimpleGUI", "A tray balloon notification")
    else:
        sg.popup_notify("Create the tray first")


@sg.bind_event("-S-TRAYOFF-")
def on_tray_off(window, values):
    if _TRAY["obj"] is not None:
        _TRAY["obj"].close()
        _TRAY["obj"] = None
        log("tray closed")


@sg.bind_event("-S-COPY-")
def on_copy(window, values):
    window.clipboard_set(f"TkSimpleGUI clipboard demo {time.time()}")
    log("clipboard written")


@sg.bind_event("-S-PASTE-")
def on_paste(window, values):
    log(f"clipboard: {window.clipboard_get()!r}")


@sg.bind_event("-S-SAVE-")
def on_save_state(window, values):
    _PREFS.set("last_theme", sg.theme())
    _PREFS.set("last_seen", time.strftime("%Y-%m-%d %H:%M:%S"))
    log(f"UserSettings saved: last_theme={_PREFS.get('last_theme')!r}, "
        f"last_seen={_PREFS.get('last_seen')}")


@sg.bind_event("-S-I18N-")
def on_i18n(window, values):
    sg.set_translations({"Open": "Ouvert", "Save": "Sauve"})
    sample = [sg._("Open"), sg._("Save"), sg._("Unknown stays")]
    log(f"i18n: {' / '.join(sample)}")
    sg.clear_translations()


# menu / toolbar / right-click shared actions
@sg.bind_event("-ACT-OPEN-")
def on_open(window, values):
    path = sg.popup_get_file("Open (Ctrl+O)")
    log(f"Action open file: {path!r}")


@sg.bind_event("-ACT-SAVE-")
def on_save(window, values):
    path = sg.popup_get_file("Save (Ctrl+S)", save_as=True)
    log(f"Action save file: {path!r}")


@sg.bind_event("-ACT-CLEAR-")
def on_clear_log(window, values):
    window["-LOG-"].clear()
    log("log cleared")


@sg.bind_event("-ACT-ABOUT-")
def on_about(window, values):
    sg.popup_ok(
        f"TkSimpleGUI {sg.__version__}\n\nOO rewrite forked from PySimpleGUI 4.x\n"
        "zero dependencies / Python 3.7+ / native default look",
        title="About")


@sg.bind_event("Copy log")
def on_copy_log(window, values):
    window.clipboard_set(window["-LOG-"].get())
    sg.popup_notify("Log copied to clipboard")


@sg.bind_event(["Native look", "DarkBlue3 theme"])
def on_theme(window, event, values):
    if event == "DarkBlue3 theme":
        name = sg.theme("DarkBlue3")
    else:
        name = sg.theme(None)
    log(f"theme switched to {name} (applies to new windows)", color="#1565c0")


@sg.bind_event("-TOOL-NEW-")
def on_tool_new(window, values):
    log("toolbar: New")


@sg.bind_event("Exit")
def on_exit(window, values):
    if _TRAY["obj"] is not None:
        _TRAY["obj"].close()
        _TRAY["obj"] = None
    sg.Window.close_all()


# ---------------------------------------------------------------- entry --
def main(argv=None):
    sg.set_dpi_awareness()  # crisp rendering on Windows high-DPI (once per process)
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
        sg.Window.close_all()
    return 0


if __name__ == "__main__":
    sys.exit(main())
