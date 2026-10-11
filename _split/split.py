# -*- coding: utf-8 -*-
"""Split the clean baseline monolith (_split/baseline.py) into src/pysimplegui package.

Strategy:
- slice top-level AST nodes (with attached comment banners) into target modules
- rewrite references to cross-module mutable globals (declared via `global`) as
  `_c.<name>` attribute access so runtime mutation semantics match the monolith
- compute cross-module references on the REWRITTEN trees
- imports that are needed at module-evaluation time (class bases, decorators,
  argument defaults, annotations, class bodies) go at the top; the top graph
  must stay acyclic
- runtime-only references are added as top imports when that keeps the graph
  acyclic, otherwise they are deferred to the bottom of the importing module
"""
import ast
import io
import os
import sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SRC = "_split/baseline.py"
OUT = os.path.join("src", "pysimplegui4")
IMPORT_RANGE = (4, 34)  # stdlib imports (sorted block)
TYPING_RANGE = (47, 67)  # typing try/except fallback
VERSION_SLICE = (70, 76)  # INFO block: port/__version__/__license__/__author__/__email__
DOC_ART = (78, 135)  # ascii art + package docstring
DOCSTRING_NODE = 86
LOGGING_ZONE = (40, 45)  # per-module logging setup, replaced by generated snippet
TAIL_START = 36091  # baseline nodes from here (except __main__) go to __init__

text = open(SRC, encoding="utf-8").read()
lines = text.splitlines(keepends=True)
tree = ast.parse(text)

# ---------------------------------------------------------------- classification
ELEM = "elements."
ALIASES_TO_INIT = {
    "ChangeLookAndFeel", "ConvertArgsToSingleString", "EasyPrint", "Print",
    "eprint", "sgprint", "PrintClose", "sgprint_close", "EasyPrintClose",
    "FillFormWithValues", "GetComplimentaryHex", "ListOfLookAndFeelValues",
    "ObjToString", "ObjToStringSingleObj", "OneLineProgressMeter",
    "OneLineProgressMeterCancel", "Popup", "PopupNoFrame", "popup_no_frame",
    "PopupNoBorder", "popup_no_border", "PopupAnnoying", "popup_annoying",
    "PopupAnimated", "PopupAutoClose", "PopupCancel", "PopupError",
    "PopupGetFile", "PopupGetFolder", "PopupGetText", "PopupNoButtons",
    "PopupNoTitlebar", "PopupNoWait", "popup_no_wait", "PopupNonBlocking",
    "PopupOK", "PopupOKCancel", "PopupQuick", "PopupQuickMessage",
    "PopupScrolled", "PopupTimed", "popup_timed", "PopupYesNo", "RGB",
    "SetGlobalIcon", "SetOptions", "sprint", "ScrolledTextBox", "TimerStart",
    "TimerStop", "test", "sdk_help", "FlexForm",
}
EXPLICIT = {
    "tclversion_detailed": "core.constants",
    "port": "_version", "__version__": "_version", "__license__": "_version",
    "__author__": "_version", "__email__": "_version",
    "_tray_icon_error": "core.constants", "_tray_icon_success": "core.constants",
    "_tray_icon_halt": "core.constants", "_tray_icon_notallowed": "core.constants",
    "_tray_icon_stop": "core.constants", "_tray_icon_exclamation": "core.constants",
    "_tray_icon_none": "core.constants",
    "TTKPartOverrides": "core.constants", "ttk_theme_in_use": "core.constants",
    "ttk_part_mapping_dict": "core.constants",
    "ttk_part_overrides_from_options": "core.constants",
    "tkinter_keysyms": "core.constants", "ThisRow": "core.constants",
    "MAC_PATCH_DICT": "core.mac",
    "pil_import_attempted": "core.constants", "pil_imported": "core.constants",
    "button_color_to_tuple": "elements.base",
    "_simplified_dual_color_to_tuple": "elements.base",
    "ToolTip": "elements.base", "Element": "elements.base",
    "convert_args_to_single_string": "core.helpers",
    "set_global_icon": "progress",
    "Input": ELEM + "input", "In": ELEM + "input", "InputText": ELEM + "input",
    "I": ELEM + "input", "Combo": ELEM + "input", "InputCombo": ELEM + "input",
    "DropDown": ELEM + "input", "Drop": ELEM + "input", "DD": ELEM + "input",
    "OptionMenu": ELEM + "input", "InputOptionMenu": ELEM + "input",
    "Listbox": ELEM + "input", "LBox": ELEM + "input", "LB": ELEM + "input",
    "Radio": ELEM + "input", "R": ELEM + "input", "Rad": ELEM + "input",
    "Checkbox": ELEM + "input", "CB": ELEM + "input", "CBox": ELEM + "input",
    "Check": ELEM + "input", "Spin": ELEM + "input", "Sp": ELEM + "input",
    "Multiline": ELEM + "multiline", "ML": ELEM + "multiline",
    "MLine": ELEM + "multiline", "Text": ELEM + "multiline",
    "Txt": ELEM + "multiline", "T": ELEM + "multiline",
    "StatusBar": ELEM + "multiline", "SBar": ELEM + "multiline",
    "Output": ELEM + "multiline",
    "Button": ELEM + "button", "B": ELEM + "button", "Btn": ELEM + "button",
    "ButtonMenu": ELEM + "button", "BMenu": ELEM + "button",
    "BM": ELEM + "button", "ProgressBar": ELEM + "button",
    "PBar": ELEM + "button", "Prog": ELEM + "button", "Progress": ELEM + "button",
    "Image": ELEM + "image", "Im": ELEM + "image", "Canvas": ELEM + "image",
    "Graph": ELEM + "graph", "G": ELEM + "graph",
    "Frame": ELEM + "container", "Fr": ELEM + "container",
    "VerticalSeparator": ELEM + "container", "VSeperator": ELEM + "container",
    "VSeparator": ELEM + "container", "VSep": ELEM + "container",
    "HorizontalSeparator": ELEM + "container", "HSeparator": ELEM + "container",
    "HSep": ELEM + "container", "Sizegrip": ELEM + "container",
    "SGrip": ELEM + "container", "Tab": ELEM + "container",
    "TabGroup": ELEM + "container", "Slider": ELEM + "container",
    "Sl": ELEM + "container", "TkFixedFrame": ELEM + "container",
    "TkScrollableFrame": ELEM + "container", "Column": ELEM + "container",
    "Col": ELEM + "container", "Pane": ELEM + "container",
    "Menu": ELEM + "container", "MenuBar": ELEM + "container",
    "Menubar": ELEM + "container", "ErrorElement": ELEM + "container",
    "Table": ELEM + "data", "Tree": ELEM + "data", "TreeData": ELEM + "data",
    "TKProgressBar": ELEM + "tkwidgets", "TKCalendar": ELEM + "tkwidgets",
    "Push": ELEM + "layout", "P": ELEM + "layout", "Stretch": ELEM + "layout",
    "VPush": ELEM + "layout", "VStretch": ELEM + "layout", "VP": ELEM + "layout",
    "Sizer": ELEM + "layout", "pin": ELEM + "layout", "vtop": ELEM + "layout",
    "vcenter": ELEM + "layout", "vbottom": ELEM + "layout",
    "Titlebar": ELEM + "layout", "MenubarCustom": ELEM + "layout",
    "FolderBrowse": ELEM + "browse", "FileBrowse": ELEM + "browse",
    "FilesBrowse": ELEM + "browse", "FileSaveAs": ELEM + "browse",
    "SaveAs": ELEM + "browse", "Save": ELEM + "browse", "Submit": ELEM + "browse",
    "Open": ELEM + "browse", "OK": ELEM + "browse", "Ok": ELEM + "browse",
    "Cancel": ELEM + "browse", "Quit": ELEM + "browse", "Exit": ELEM + "browse",
    "Yes": ELEM + "browse", "No": ELEM + "browse", "Help": ELEM + "browse",
    "Debug": ELEM + "browse", "SimpleButton": ELEM + "browse",
    "CloseButton": ELEM + "browse", "CButton": ELEM + "browse",
    "ReadButton": ELEM + "browse", "ReadFormButton": ELEM + "browse",
    "RButton": ELEM + "browse", "RealtimeButton": ELEM + "browse",
    "DummyButton": ELEM + "browse", "CalendarButton": ELEM + "browse",
    "ColorChooserButton": ELEM + "browse",
    "_TimerPeriodic": "window.window", "Window": "window.window",
    "_long_func_thread": "window.window", "_exit_mainloop": "window.window",
    "_timeout_alarm_callback_hidden": "window.window",
    "read_all_windows": "window.window",
    "AddToReturnDictionary": "window.results",
    "AddToReturnList": "window.results", "InitializeResults": "window.results",
    "DecodeRadioRowCol": "window.results", "EncodeRadioRowCol": "window.results",
    "_BuildResults": "window.results", "_BuildResultsForSubform": "window.results",
    "fill_form_with_values": "window.results",
    "_FindElementWithFocusInSubForm": "window.results",
    "AddMenuItem": "window.results", "VarHolder": "window.results",
    "_fixed_map": "window.build", "_add_right_click_menu": "window.build",
    "_change_ttk_theme": "window.build", "_make_ttk_style_name": "window.build",
    "_make_ttk_scrollbar": "window.build", "PackFormIntoFrame": "window.build",
    "_get_hidden_master_root": "window.build", "_no_titlebar_setup": "window.build",
    "_convert_window_to_tk": "window.build", "StartupTK": "window.build",
    "_set_icon_for_tkinter_window": "window.build",
    "_GetNumLinesNeeded": "window.build", "SystemTray": "window.system_tray",
    "popup": "popup.popups_core", "MsgBox": "popup.popups_core",
    "popup_scrolled": "popup.popups_core", "popup_no_buttons": "popup.popups_core",
    "popup_non_blocking": "popup.popups_core", "popup_quick": "popup.popups_core",
    "popup_quick_message": "popup.popups_core",
    "popup_no_titlebar": "popup.popups_standard",
    "popup_auto_close": "popup.popups_standard",
    "popup_error": "popup.popups_standard", "popup_cancel": "popup.popups_standard",
    "popup_ok": "popup.popups_standard", "popup_ok_cancel": "popup.popups_standard",
    "popup_yes_no": "popup.popups_standard",
    "popup_get_folder": "popup.popups_input", "popup_get_file": "popup.popups_input",
    "popup_get_text": "popup.popups_input", "popup_get_date": "popup.popups_input",
    "popup_animated": "popup.popups_special", "popup_notify": "popup.popups_special",
    "popup_menu": "popup.popups_special",
    "popup_error_with_traceback": "popup.popups_special",
    "_error_popup_with_traceback": "popup.popups_special",
    "_error_popup_with_code": "popup.popups_special",
    "_process_thread": "popup.popups_special",
    "shell_with_animation": "popup.popups_special",
    "_create_error_message": "popup.popups_special",
    "LOOK_AND_FEEL_TABLE": "theme.theme",
    "list_of_look_and_feel_values": "theme.theme", "theme": "theme.theme",
    "theme_background_color": "theme.theme",
    "theme_element_background_color": "theme.theme",
    "theme_text_color": "theme.theme",
    "theme_text_element_background_color": "theme.theme",
    "theme_input_background_color": "theme.theme",
    "theme_input_text_color": "theme.theme",
    "theme_button_color": "theme.theme",
    "theme_button_color_background": "theme.theme",
    "theme_button_color_text": "theme.theme",
    "theme_progress_bar_color": "theme.theme",
    "theme_slider_color": "theme.theme", "theme_border_width": "theme.theme",
    "theme_slider_border_width": "theme.theme",
    "theme_progress_bar_border_width": "theme.theme",
    "theme_element_text_color": "theme.theme", "theme_list": "theme.theme",
    "theme_add_new": "theme.theme", "theme_use_custom_titlebar": "theme.theme",
    "theme_global": "theme.theme", "theme_previewer": "theme.theme",
    "preview_all_look_and_feel_themes": "theme.theme",
    "_theme_preview_window_swatches": "theme.theme",
    "theme_previewer_swatches": "theme.theme",
    "change_look_and_feel": "theme.theme",
    "TRANSPARENT_BUTTON": "theme.theme",
    "set_options": "settings.options", "UserSettings": "settings.user_settings",
    "pysimplegui_user_settings": "settings.user_settings",
    "execute_command_subprocess": "settings.execute",
    "execute_py_file": "settings.execute",
    "execute_py_get_interpreter": "settings.execute",
    "execute_py_get_running_interpreter": "settings.execute",
    "execute_editor": "settings.execute", "execute_get_results": "settings.execute",
    "execute_subprocess_still_running": "settings.execute",
    "execute_file_explorer": "settings.execute",
    "execute_find_callers_filename": "settings.execute",
    "_create_full_editor_command": "settings.execute",
    "execute_get_editor": "settings.execute",
    "user_settings_filename": "settings.user_settings",
    "user_settings_delete_filename": "settings.user_settings",
    "user_settings_set_entry": "settings.user_settings",
    "user_settings_delete_entry": "settings.user_settings",
    "user_settings_get_entry": "settings.user_settings",
    "user_settings_save": "settings.user_settings",
    "user_settings_load": "settings.user_settings",
    "user_settings_file_exists": "settings.user_settings",
    "user_settings_write_new_dictionary": "settings.user_settings",
    "user_settings_silent_on_error": "settings.user_settings",
    "user_settings": "settings.user_settings",
    "user_settings_object": "settings.user_settings",
    "_read_mac_global_settings": "core.mac",
    "_mac_should_apply_notitlebar_patch": "core.mac",
    "_mac_should_set_alpha_to_99": "core.mac",
    "main_mac_feature_control": "core.mac",
    "_QuickMeter": "progress", "one_line_progress_meter": "progress",
    "one_line_progress_meter_cancel": "progress", "easy_print": "progress",
    "easy_print_close": "progress",
    "cprint_set_output_destination": "progress", "cprint": "progress",
    "_print_to_element": "progress", "_parse_colors_parm": "progress",
    "red_x": "debugger.debugger", "_DebugWin": "debugger.debugger",
    "_Debugger": "debugger.debugger", "show_debugger_window": "debugger.debugger",
    "show_debugger_popout_window": "debugger.debugger",
    "_refresh_debugger": "debugger.debugger",
    "_debugger_window_is_open": "debugger.debugger",
    "get_versions": "debugger.debugger",
    "_random_error_emoji": "debugger.emoji", "_random_happy_emoji": "debugger.emoji",
    "g_time_start": "utils.timer", "g_time_end": "utils.timer",
    "g_time_delta": "utils.timer", "timer_start": "utils.timer",
    "timer_stop": "utils.timer", "timer_stop_usec": "utils.timer",
    "_timeit": "utils.timer", "_timeit_counter": "utils.timer",
    "MAX_TIMEIT_COUNT": "utils.timer", "_timeit_total": "utils.timer",
    "_timeit_summary": "utils.timer", "formatted_datetime_now": "utils.timer",
    "running_linux": "utils.platform", "running_mac": "utils.platform",
    "running_windows": "utils.platform", "running_trinket": "utils.platform",
    "running_replit": "utils.platform", "rgb": "utils.color",
    "get_complimentary_hex": "utils.color", "_hex_to_hsl": "utils.color",
    "_hex_to_rgb": "utils.color", "_rgb_to_hsl": "utils.color",
    "_hsl_to_rgb": "utils.color", "_hsv_to_hsl": "utils.color",
    "_hsl_to_hsv": "utils.color",
    "obj_to_string_single_obj": "utils.obj", "obj_to_string": "utils.obj",
    "clipboard_set": "utils.misc", "clipboard_get": "utils.misc",
    "singleton_window": "event", "PySimpleEvent": "event",
    "_main_entry_point": "cli", "main_get_debug_data": "cli",
    "_global_settings_get_ttk_scrollbar_info": "cli",
    "_global_settings_get_watermark_info": "cli",
    "main_global_get_screen_snapshot_symcode": "cli",
    "main_global_pysimplegui_settings_erase": "cli",
    "main_global_pysimplegui_settings": "cli", "main_sdk_help": "cli",
    "_main_switch_theme": "cli", "_create_main_window": "cli", "main": "cli",
}
IF_MAP = {647: "core.constants", 32261: "settings.user_settings"}
EMOJI_PREFIX = ("EMOJI_BASE64_", "HEART_", "PYTHON_COLORED_HEARTS", "RED_X_BASE64",
                "GREEN_CHECK_BASE64", "ICON_BUY_ME_A_COFFEE")

def classify(name, kind, lineno):
    if name in EXPLICIT:
        return EXPLICIT[name]
    if name in ALIASES_TO_INIT:
        return "__init__"
    if kind == "assign":
        if name.startswith(EMOJI_PREFIX):
            return "debugger.emoji"
        if name == name.upper() and name.isidentifier():
            return "core.constants"
    return None

# ---------------------------------------------------------------- collect nodes
entries = []
unmapped = []
prev_end = 0
for node in tree.body:
    lineno, end = node.lineno, node.end_lineno
    if lineno <= IMPORT_RANGE[1] or lineno == DOCSTRING_NODE:
        prev_end = end
        continue
    if LOGGING_ZONE[0] <= lineno <= LOGGING_ZONE[1]:
        prev_end = end
        continue
    if VERSION_SLICE[0] <= lineno <= VERSION_SLICE[1]:
        prev_end = end
        continue
    if lineno <= TYPING_RANGE[1] and isinstance(node, (ast.Import, ast.ImportFrom, ast.Try)):
        prev_end = end
        continue
    kind, names, module = None, [], None
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        kind, names = "func", [node.name]
    elif isinstance(node, ast.ClassDef):
        kind, names = "class", [node.name]
    elif isinstance(node, ast.Assign):
        kind = "assign"
        for t in node.targets:
            if isinstance(t, ast.Name):
                names.append(t.id)
            elif isinstance(t, ast.Tuple):
                names.extend(e.id for e in t.elts if isinstance(e, ast.Name))
    elif isinstance(node, ast.If):
        seg = ast.get_source_segment(text, node.test) or ""
        if "__main__" in seg:
            kind, names, module = "main", ["__main__block"], "cli"
        elif lineno >= TAIL_START:
            kind, names, module = "expr", ["__tail_%d" % lineno], "__init__"
        else:
            kind, names, module = "if", ["__if_%d" % lineno], IF_MAP.get(lineno)
    else:
        kind, names = "expr", ["__expr_%d" % lineno]
    if module is None and names and not names[0].startswith("__expr_"):
        module = classify(names[0], kind, lineno)
    if module is None and not names[0].startswith("__expr_"):
        unmapped.append((names, kind, lineno))
        prev_end = end
        continue
    entries.append((names, kind, node, module))
    prev_end = end

if unmapped:
    print("UNMAPPED top-level nodes:")
    for names, kind, lineno in unmapped:
        print("  {} {} @{}".format(kind, names, lineno))
    sys.exit(1)

resolved = []
orphan_buf = []
for names, kind, node, module in entries:
    if module is None:
        orphan_buf.append((names, kind, node))
        continue
    for o in orphan_buf:
        resolved.append((o[0], o[1], o[2], module))
    orphan_buf = []
    resolved.append((names, kind, node, module))
for o in orphan_buf:
    resolved.append((o[0], o[1], o[2], "core.constants"))
entries = resolved

# ---------------------------------------------------------------- slicing
def slice_start(node, prev_end):
    s = node.lineno
    while s - 1 > prev_end:
        line = lines[s - 2].strip()
        if line == "" or line.startswith("#"):
            s -= 1
        else:
            break
    return s

modules = defaultdict(list)
prev_end = VERSION_SLICE[1]
order = []
for names, kind, node, module in entries:
    start = slice_start(node, prev_end)
    modules[module].append((node, start, node.end_lineno))
    prev_end = max(prev_end, node.end_lineno)
    if module not in order:
        order.append(module)

# ---------------------------------------------------------------- defined names
defnames = {}
for names, kind, node, module in entries:
    for n in names:
        if n.startswith("__"):
            continue
        if n in defnames and defnames[n] != module:
            print("DUP DEF: {} in {} and {}".format(n, defnames[n], module))
        defnames[n] = module

# ---------------------------------------------------------------- mutable globals
node_module = {}
for names, kind, node, module in entries:
    node_module[id(node)] = module

global_sites = defaultdict(set)
for node in tree.body:
    mod = node_module.get(id(node))
    if mod in (None, "__init__"):
        continue
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        for sub in ast.walk(node):
            if isinstance(sub, ast.Global):
                for n in sub.names:
                    global_sites[n].add(mod)

rewrite_names = set()
for name, sites in global_sites.items():
    owner = defnames.get(name)
    if owner is None or any(s != owner for s in sites):
        rewrite_names.add(name)
print("REWRITE set ({}): {}".format(len(rewrite_names), ", ".join(sorted(rewrite_names))))

# ---------------------------------------------------------------- rewrite pass
def collect_scope(n):
    loc, glo = set(), set()
    args = getattr(n, "args", None)
    if args:
        for ar in list(args.args) + list(args.kwonlyargs):
            loc.add(ar.arg)
        if args.vararg:
            loc.add(args.vararg.arg)
        if args.kwarg:
            loc.add(args.kwarg.arg)
    def stmt_walk(s):
        if isinstance(s, ast.Global):
            glo.update(s.names)
        elif isinstance(s, ast.Name) and isinstance(s.ctx, (ast.Store, ast.Del)):
            loc.add(s.id)
        elif isinstance(s, ast.arg):
            loc.add(s.arg)
        elif isinstance(s, ast.ExceptHandler) and s.name:
            loc.add(s.name)
        for child in ast.iter_child_nodes(s):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                if not isinstance(child, ast.Lambda):
                    loc.add(child.name)
                continue
            stmt_walk(child)
    body = getattr(n, "body", None)
    if isinstance(n, ast.Lambda):
        stmt_walk(n.body)
    elif body:
        for stmt in body:
            stmt_walk(stmt)
    return loc, glo

def build_scopes(root):
    scopes = []
    def walk(n):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            loc, glo = collect_scope(n)
            scopes.append((n.lineno, n.end_lineno, loc, glo))
        for child in ast.iter_child_nodes(n):
            walk(child)
    walk(root)
    return scopes

def apply_rewrites(chunk_text, module):
    if not rewrite_names and not alias_subst:
        return chunk_text
    chunk_tree = ast.parse(chunk_text)
    scopes = build_scopes(chunk_tree)
    edits = []  # (lineno, col_start, col_end, replacement)
    for sub in ast.walk(chunk_tree):
        if not isinstance(sub, ast.Name):
            continue
        if sub.id in rewrite_names:
            if defnames.get(sub.id) == module:
                continue  # definition lives in this module, keep bare name
            local = False
            for (s0, s1, loc, glo) in scopes:
                if s0 <= sub.lineno <= s1 and sub.id in loc and sub.id not in glo:
                    local = True
                    break
            if not local:
                edits.append((sub.lineno, sub.col_offset, sub.end_col_offset, "_c." + sub.id))
        elif isinstance(sub.ctx, ast.Load) and sub.id in alias_subst:
            local = False
            for (s0, s1, loc, glo) in scopes:
                if s0 <= sub.lineno <= s1 and sub.id in loc:
                    local = True
                    break
            if not local:
                edits.append((sub.lineno, sub.col_offset, sub.end_col_offset, alias_subst[sub.id]))
    if not edits:
        return chunk_text
    tl = chunk_text.splitlines(keepends=True)
    by_line = defaultdict(list)
    for ln, c0, c1, rep in edits:
        by_line[ln].append((c0, c1, rep))
    for ln, spans in by_line.items():
        line = tl[ln - 1]
        for c0, c1, rep in sorted(spans, reverse=True):
            line = line[:c0] + rep + line[c1:]
        tl[ln - 1] = line
    return "".join(tl)

# alias substitution table: internal code must use canonical names
alias_subst = {}
for names, kind, node, module in entries:
    if module == "__init__" and kind == "assign" and isinstance(node, ast.Assign):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and isinstance(node.value, ast.Name):
            alias_subst[node.targets[0].id] = node.value.id

# per-module chunk text and rewritten trees
chunk_text = {}
rewritten = {}
rtrees = {}
for m, chunks in modules.items():
    src = "".join("".join(lines[s - 1:e]) for (n, s, e) in chunks)
    chunk_text[m] = src
    rewritten[m] = apply_rewrites(src, m)
    rtrees[m] = ast.parse(rewritten[m])

# warn about class-body stores of mutable globals (direct statements only)
for m, t in rtrees.items():
    for sub in ast.walk(t):
        if isinstance(sub, ast.ClassDef):
            for st in sub.body:
                if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue
                for x in ast.walk(st):
                    if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store) and x.id in rewrite_names:
                        print("WARN class-body store of mutable global {} in {} at line {}".format(x.id, m, x.lineno))

# ---------------------------------------------------------------- references
mod_refs = defaultdict(set)
for m, t in rtrees.items():
    for sub in ast.walk(t):
        if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
            r = sub.id
            if r in defnames and defnames[r] != m:
                mod_refs[m].add(r)

mod_defs = defaultdict(set)
for n, m in defnames.items():
    mod_defs[m].add(n)

problems = []
for m, refs in mod_refs.items():
    for r in refs:
        if defnames[r] == "__init__":
            problems.append("{} references __init__ alias {!r}".format(m, r))
for p in problems:
    print("PROBLEM:", p)
if problems:
    sys.exit(1)

# ---------------------------------------------------------------- scope of eval
def module_level_uses(tree_of_module, names):
    """Names referenced at module/class evaluation time (bases, decorators,
    defaults, annotations, class/module body statements). Function bodies are
    runtime-only."""
    hits = set()

    def walk(n, in_func):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            for d in n.decorator_list:
                walk(d, in_func)
            args = n.args
            for d in list(args.defaults) + [d for d in args.kw_defaults if d]:
                walk(d, in_func)
            anns = [a.annotation for a in list(args.args) + list(args.kwonlyargs) if a.annotation]
            if args.vararg is not None and args.vararg.annotation:
                anns.append(args.vararg.annotation)
            if args.kwarg is not None and args.kwarg.annotation:
                anns.append(args.kwarg.annotation)
            if getattr(n, "returns", None):
                anns.append(n.returns)
            for ann in anns:
                walk(ann, in_func)
            return
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in names:
            hits.add(n.id)
        for child in ast.iter_child_nodes(n):
            walk(child, in_func)

    for top in tree_of_module.body:
        walk(top, False)
    return hits

def reaches(start, target, graph):
    seen = set()
    stack = [start]
    while stack:
        cur = stack.pop()
        if cur == target:
            return True
        for nxt in graph.get(cur, ()):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return False

# ---------------------------------------------------------------- import plan
top_edges = defaultdict(set)          # module -> providers imported at top
top_names = defaultdict(lambda: defaultdict(set))   # module -> provider -> names
bottom_names = defaultdict(lambda: defaultdict(set))  # module -> provider -> names

external = {}
for m in modules:
    own = mod_defs.get(m, set())
    external[m] = set(mod_refs.get(m, ()))

# 1. module-eval references must be top imports
eval_names = {}
for m in modules:
    eval_names[m] = module_level_uses(rtrees[m], external[m])
    for r in eval_names[m]:
        p = defnames[r]
        if p == m or p == "__init__":
            continue
        top_edges[m].add(p)
        top_names[m][p].add(r)

# the eval-only graph must be acyclic
def find_cycle(graph):
    seen, stack_path = set(), []

    def dfs(node):
        stack_path.append(node)
        seen.add(node)
        for nxt in sorted(graph.get(node, ())):
            if nxt in stack_path:
                return stack_path[stack_path.index(nxt):] + [nxt]
            if nxt not in seen:
                c = dfs(nxt)
                if c:
                    return c
        stack_path.pop()
        return None

    for m in sorted(graph):
        c = dfs(m)
        if c:
            return c
    return None

cyc = find_cycle(top_edges)
if cyc:
    print("HARD CYCLE in module-eval imports: " + " -> ".join(cyc))
    sys.exit(1)

# 2. all runtime-only references become lazy (function-level) imports; the
#    top graph keeps only module-eval-required edges and is acyclic by check
for m in sorted(modules):
    evalset = eval_names[m]
    for r in sorted(mod_refs.get(m, ())):
        if r in evalset:
            continue
        p = defnames[r]
        if p == m or p == "__init__":
            continue
        bottom_names[m][p].add(r)

deferred = sorted((m, p) for m in bottom_names for p in bottom_names[m])
if deferred:
    print("Deferred (lazy, function-level) imports:")
    for m, p in deferred:
        print("  {} -> {} [{}]".format(m, p, ", ".join(sorted(bottom_names[m][p]))))

# ---------------------------------------------------------------- lazy imports
def provider_modpath(module, provider):
    ap = module.split(".")
    bp = provider.split(".")
    if ap[:-1] == bp[:-1] and len(ap) > 1:
        return "." + bp[-1]
    common = 0
    while common < min(len(ap), len(bp)) - 1 and ap[common] == bp[common]:
        common += 1
    return "." * (len(ap) - common) + ".".join(bp[common:])

# deferred (bottom) imports cannot break import-time cycles - convert them to
# function-level imports inserted after each using function's docstring
lazy_body = {}
for m in list(bottom_names.keys()):
    prov_of = {}
    for p, names in bottom_names[m].items():
        for n in names:
            prov_of[n] = p
    deferred_set = set(prov_of)
    inserts = []
    for fn in ast.walk(rtrees[m]):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        loc, glo = collect_scope(fn)
        needed = defaultdict(set)
        for sub in ast.walk(fn):
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load) and sub.id in deferred_set:
                if sub.id in loc and sub.id not in glo:
                    continue  # resolves to a local binding
                needed[prov_of[sub.id]].add(sub.id)
        if not needed:
            continue
        body0 = fn.body[0]
        if isinstance(body0, ast.Expr) and isinstance(body0.value, ast.Constant) and isinstance(body0.value.value, str):
            pos = body0.end_lineno
        else:
            pos = body0.lineno - 1
        indent = " " * body0.col_offset
        block = ""
        for p in sorted(needed):
            block += "{}from {} import {}\n".format(
                indent, provider_modpath(m, p), ", ".join(sorted(needed[p])))
        inserts.append((pos, block))
    tl = rewritten[m].splitlines(keepends=True)
    for pos, block in sorted(inserts, key=lambda x: -x[0]):
        tl.insert(pos, block)
    lazy_body[m] = "".join(tl)

# ---------------------------------------------------------------- emit helpers
def provider_import(module, provider, names):
    ap = module.split(".")
    bp = provider.split(".")
    if ap[:-1] == bp[:-1] and len(ap) > 1:
        return "from .{} import {}".format(bp[-1], ", ".join(sorted(names)))
    common = 0
    while common < min(len(ap), len(bp)) - 1 and ap[common] == bp[common]:
        common += 1
    up = len(ap) - common
    down = ".".join(bp[common:])
    return "from {}{} import {}".format("." * up, down, ", ".join(sorted(names)))

def module_header(module):
    out = []
    out.append('#!/usr/bin/env python3\n')
    out.append('"""PySimpleGUI4 - {}.\n\nSplit from the PySimpleGUI4 monolith. Part of the modular\npysimplegui4 package; Python 3.4+ compatible.\n"""\n\n'.format(module))
    out.append("".join(lines[IMPORT_RANGE[0] - 1:IMPORT_RANGE[1]]))
    out.append("\nimport logging\n\n_logger = logging.getLogger(__name__)\n")
    if module == "core.constants":
        out.append(
            '_package_logger = logging.getLogger("pysimplegui4")\n'
            "_package_logger.setLevel(logging.INFO)\n"
            "if not _package_logger.handlers:\n"
            "    _package_handler = logging.StreamHandler()\n"
            '    _package_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))\n'
            "    _package_logger.addHandler(_package_handler)\n"
        )
    out.append("".join(lines[TYPING_RANGE[0] - 1:TYPING_RANGE[1]]))
    out.append("\n")
    return out

def emit_module(module):
    out = module_header(module)
    if "_c." in rewritten[module]:
        prefix = "." * (module.count(".") + 1)
        out.append("from {}core import constants as _c\n".format(prefix))
    for p in sorted(top_names[module]):
        out.append(provider_import(module, p, top_names[module][p]) + "\n")
    out.append("\n\n")
    body = lazy_body.get(module, rewritten[module])
    if not body.endswith("\n"):
        body += "\n"
    out.append(body)
    publics = sorted(n for n in mod_defs.get(module, ()) if not n.startswith("_"))
    if publics:
        out.append("\n\n__all__ = [\n")
        for p in publics:
            out.append('    "{}",\n'.format(p))
        out.append("]\n")
    return "".join(out)

# ---------------------------------------------------------------- write files
SUBPACKAGES = ["core", "utils", "elements", "window", "popup", "theme", "settings", "debugger"]
for sp in SUBPACKAGES:
    os.makedirs(os.path.join(OUT, sp), exist_ok=True)
os.makedirs(OUT, exist_ok=True)

written = []
for module in order:
    if module in ("__init__", "_version"):
        continue
    path = os.path.join(OUT, module.replace(".", os.sep) + ".py")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    content = emit_module(module)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    written.append((module, path, content.count("\n")))

for sp in SUBPACKAGES:
    members = sorted(m for m in order if m.split(".")[0] == sp and m.count(".") == 1)
    out = ['#!/usr/bin/env python3\n"""PySimpleGUI4 {} subpackage."""\n\n'.format(sp)]
    for m in members:
        leaf = m.split(".", 1)[1]
        out.append("from .{} import *  # noqa: F401,F403\n".format(leaf))
    seen = []
    for m in members:
        for n in sorted(mod_defs.get(m, ())):
            if not n.startswith("_") and n not in seen:
                seen.append(n)
    out.append("\n__all__ = [\n")
    for n in seen:
        out.append('    "{}",\n'.format(n))
    out.append("]\n")
    with open(os.path.join(OUT, sp, "__init__.py"), "w", encoding="utf-8", newline="") as f:
        f.write("".join(out))
    written.append((sp + ".__init__", os.path.join(OUT, sp, "__init__.py"), len(seen)))

# root __init__
init = []
init.append("".join(lines[DOC_ART[0] - 1:DOC_ART[1]]))
init.append("\n\n")
init.append("".join(lines[IMPORT_RANGE[0] - 1:IMPORT_RANGE[1]]))
init.append("\n\n")
init.append("from ._version import __version__, version, port, __license__, __author__, __email__\n\n")
init.append("from .core import constants as _c  # noqa: F401\n\n")
for sp in SUBPACKAGES:
    init.append("from .{} import *  # noqa: F401,F403\n".format(sp))
for flat in ("event", "progress", "cli"):
    init.append("from .{} import *  # noqa: F401,F403\n".format(flat))
# private names used by the tail blocks are not covered by star imports
priv_by_prov = defaultdict(set)
for sub in ast.walk(rtrees["__init__"]):
    if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
        n = sub.id
        if n in defnames and defnames[n] != "__init__" and n.startswith("_"):
            priv_by_prov[defnames[n]].add(n)
if priv_by_prov:
    init.append("\n")
    for p in sorted(priv_by_prov):
        init.append(provider_import("__init__", p, priv_by_prov[p]) + "\n")
init.append("\n\n")
for names, kind, node, module in entries:
    if module != "__init__":
        continue
    start = None
    for (n, s, e) in modules["__init__"]:
        if n is node:
            start = s
    chunk = apply_rewrites("".join(lines[start - 1:node.end_lineno]), "__init__")
    if not chunk.endswith("\n"):
        chunk += "\n"
    init.append(chunk + "\n")
root_all = []
for sp in SUBPACKAGES:
    for m in sorted(mod_defs):
        if m.split(".")[0] == sp and m.count(".") == 1:
            root_all.extend(sorted(n for n in mod_defs[m] if not n.startswith("_")))
for m in ("event", "progress", "cli"):
    root_all.extend(sorted(n for n in mod_defs.get(m, ()) if not n.startswith("_")))
root_all.extend(sorted(ALIASES_TO_INIT))
seen = []
for n in root_all:
    if n not in seen:
        seen.append(n)
init.append("\n__all__ = [\n")
for n in seen:
    init.append('    "{}",\n'.format(n))
init.append("]\n")
with open(os.path.join(OUT, "__init__.py"), "w", encoding="utf-8", newline="") as f:
    f.write("".join(init))
written.append(("__init__", os.path.join(OUT, "__init__.py"), len("".join(init).splitlines())))

# _version.py
ver = ['#!/usr/bin/env python3\n"""PySimpleGUI4 version information."""\n\n']
ver.append("".join(lines[VERSION_SLICE[0] - 1:VERSION_SLICE[1]]))
ver.append("\nversion = __version__\n")
with open(os.path.join(OUT, "_version.py"), "w", encoding="utf-8", newline="") as f:
    f.write("".join(ver))
written.append(("_version", os.path.join(OUT, "_version.py"), VERSION_SLICE[1] + 4))

print("\n=== WRITTEN ===")
total = 0
for module, path, nlines in sorted(written):
    print("{:>22} {:>6} lines  {}".format(module, nlines, path))
    total += nlines
print("TOTAL:", total, "lines")
