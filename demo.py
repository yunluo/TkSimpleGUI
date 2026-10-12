#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PySimpleGUI4 全功能演示（最新标准版）。

演示**当前推荐写法**：
- ``window.run()`` —— 根对象直接启动应用，用户零事件循环
- ``@sg.default_app().bind_event`` + ``on_*`` 函数 —— 全局事件管理器分发
- ``Action`` —— 菜单/工具栏/快捷键共享动作
- ``parent=`` —— 窗口层级（子窗口演示，父关级联）
- T 前缀命名、Toast、RoundButton、TextProgressBar、Slider 气泡等新能力

运行::

    python demo.py            # 交互模式
    python demo.py --smoke    # 自检：泵 2 秒事件、自动退出
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
import PySimpleGUI4 as sg  # noqa: E402

# 16x16 P4 徽标（表格行图标 / 树节点图标用）
ICON16 = (
    b"iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAiUlEQVR42mNgQANuPQ//48MM"
    b"uIBz283/pGAUzQ6NF/+Tg+EG2Nac+k8OBmu2Kjv0nxLMYF646z8lmMEkZ/N/SjCDYdrq/5Rg"
    b"Br3Exf8pwQzaMXP+U4IZNMKm/KcEM6gG9vynBIPTgpJP639yMDwlyrvV/icHo+QHGcfS/6Rg"
    b"nLlSyibvPz6Mrh4AeY7yRAY4AssAAAAASUVORK5CYII="
)

_STOPWATCH = {"start": None}
_TRAY = {"obj": None}
_PREFS = sg.UserSettings("demo.json")

# 全局事件管理器：所有 on_* handler 注册在这里（default_app 是 .run() 的默认分发器）
app = sg.default_app()

# 运行期共享状态（handler 之间通过这里传递）
_state = {
    "window": None,          # 主窗口（build() 时填充）
    "figure_last": None,
    "figure_count": 0,
    "tree_counter": 0,
    "about_window": None,    # 独立"关于"子窗口（演示 parent 层级）
}


def log(text, color=None):
    """往底部事件日志追加一行（可着色）。"""
    window = _state["window"]
    if window is not None and "-LOG-" in window:
        window["-LOG-"].print(time.strftime("[%H:%M:%S] ") + text, text_color=color)


def require_window():
    """当前 handler 收到的 window 就是主窗口（见各 handler 第一参数）。"""
    return _state["window"]


# ---------------------------------------------------------------- 标签页布局 --
def tab_inputs():
    band_top = sg.Column([
        [sg.Column([[sg.TText("整数校验（只许数字）")],
                    [sg.TInput("", key="-IN-NUM-", size=(12, 1), validate="key",
                              validate_command=sg.validate_integer,
                              enable_events=True)]]),
         sg.Column([[sg.TText("密码")],
                    [sg.TInput("", key="-IN-PASS-", size=(12, 1), password_char="*")],
                    [sg.TCheckbox("显示密码", key="-CB-SHOW-", enable_events=True)]]),
         sg.Column([[sg.TLabeledEdit("用户名", "yunluo", key="-IN-USER-")],
                    [sg.TButton("提交表单", key="-SUBMIT-")]]),
         sg.Column([[sg.TText("微调")],
                    [sg.TSpin([str(n) for n in range(1, 11)], initial_value="5",
                              key="-SP-", enable_events=True)]])],
    ])
    band_slider = sg.Column([
        [sg.TText("滑杆联动进度条（show_value 拖动有数值气泡）：")],
        [sg.TSlider((0, 100), default_value=30, key="-SL-",
                    enable_events=True, size=(18, 15), show_value=True),
         sg.TProgressBar(100, current_value=30, size=(20, 12), key="-PB-SL-")],
    ])
    band_multiline = sg.Column([
        [sg.TMultiline("多行文本区域（支持撤销/重做/彩色输出/查找替换）\n",
                       key="-ML-", size=(56, 5))],
        [sg.TButton("彩色输出", key="-B-COLOR-"), sg.TButton("撤销", key="-B-UNDO-"),
         sg.TButton("重做", key="-B-REDO-"), sg.TButton("查找", key="-B-FIND-"),
         sg.TButton("替换", key="-B-REPLACE-"), sg.TButton("清空", key="-B-CLEAR-ML-")],
    ])
    return [[band_top], [band_slider], [band_multiline]]


def tab_selection():
    band = sg.Column([
        [sg.Column([[sg.TText("下拉")],
                    [sg.TCombo(["红色", "绿色", "蓝色"], default_value="红色",
                              key="-CMB-", enable_events=True)],
                    [sg.TText("OptionMenu")],
                    [sg.TOptionMenu(["甲", "乙", "丙"], key="-OPT-",
                                   enable_events=True)],
                    [sg.TText("微调")],
                    [sg.TSpin(["低", "中", "高"], initial_value="中",
                             key="-SP2-", enable_events=True)]],
                   ),
         sg.Column([[sg.TText("列表（多选）")],
                    [sg.TListbox(["项目一", "项目二", "项目三", "项目四"],
                                size=(14, 4), select_mode=sg.SelectMode.EXTENDED,
                                key="-LB-", enable_events=True)]]),
         sg.Column([[sg.TText("复选")],
                    [sg.TCheckbox("复选 A", key="-CBA-", enable_events=True)],
                    [sg.TCheckbox("复选 B", key="-CBB-", enable_events=True)]]),
         sg.Column([[sg.TText("勾选列表")],
                    [sg.TCheckList(["西瓜", "苹果", "香蕉"],
                                  default_checked=["苹果"], key="-CKL-",
                                  enable_events=True)],
                    [sg.TButton("全选", key="-B-CKALL-"),
                     sg.TButton("全不选", key="-B-CKNONE-")]]),
         sg.Column([[sg.TText("单选（互斥）")],
                    [sg.TRadio("方案一", "plan", default=True, key="-R1-",
                              enable_events=True)],
                    [sg.TRadio("方案二", "plan", key="-R2-", enable_events=True)],
                    [sg.TRadio("方案三", "plan", key="-R3-", enable_events=True)]])],
    ])
    return [[band]]


def tab_data():
    records = [
        {"姓名": "云落", "年龄": 30, "城市": "深圳"},
        {"姓名": "小明", "年龄": 24, "城市": "杭州"},
        {"姓名": "阿强", "年龄": 36, "城市": "成都"},
        {"姓名": "小美", "年龄": 28, "城市": "上海"},
    ]
    table = sg.TTable([], headings=[], key="-TB-", enable_edit=True,
                      row_icons=[ICON16, ICON16, ICON16, ICON16], num_rows=5,
                      auto_size_columns=False, col_widths=[10, 8, 10])
    table.bind(records)
    tree = sg.TTree(headings=["节点"], show_headings=False, num_rows=6, key="-TREE-")
    kv = sg.TKeyValueEditor([("主机", "localhost"), ("端口", "5432")], key="-KV-")
    band = sg.Column([
        [sg.Column([[sg.TText("表格：点表头排序 / 双击编辑 / 行图标 / 拖表头分隔线")],
                    [table],
                    [sg.TButton("换一批数据", key="-B-REBIND-"),
                     sg.TText("选中记录："),
                     sg.TText("", key="-T-REC-", size=(22, 1))]]),
         sg.Column([[sg.TText("树（带图标 / 分组 / 汇总行）")],
                    [tree],
                    [sg.TButton("加分组", key="-B-ADDGRP-"),
                     sg.TButton("加节点", key="-B-ADD-"),
                     sg.TButton("删节点", key="-B-DEL-")]]),
         sg.Column([[sg.TText("键值编辑器（TValEdit）")],
                    [kv],
                    [sg.TButton("读取键值", key="-B-KVGET-")]])],
    ])
    return [[band]]


def tab_graphics():
    graph = sg.TGraph((320, 160), (0, 0), (100, 54), key="-GRAPH-",
                      enable_events=True, background_color="#ffffff")
    return [
        [sg.Column([[sg.TText("TGraph（用户坐标系 + 图元句柄）—— 点击画布有反馈")],
                    [graph],
                    [sg.TButton("画圆", key="-B-CIRCLE-"),
                     sg.TButton("画矩形", key="-B-RECT-"),
                     sg.TButton("画字", key="-B-TEXT-"),
                     sg.TButton("移动图形", key="-B-MOVEF-"),
                     sg.TButton("删除最后", key="-B-DELF-"),
                     sg.TButton("清空", key="-B-CLEARG-")]])],
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
    frame = sg.TFrame("分组框 Frame", [[sg.TInput("框内输入", key="-IN-FRAME-")]],
                      key="-FRAME-")
    splitter = sg.TSplitter(
        [[[sg.TText("左窗格")], [sg.TListbox(["A", "B", "C"], size=(9, 3))]],
         [[sg.TText("右窗格（拖动分隔条）")], [sg.TInput("拖我", size=(18, 1))]]],
        key="-SPLIT-")
    scroll = sg.TScrollableColumn(
        [[sg.TText(f"  滚动行 {i:>2d} ")] for i in range(1, 21)],
        size=(140, 110), key="-SCROLL-", background_color="#f7f7f7")
    flow = sg.TFlowPanel(
        [sg.TButton(f"按钮 {i}", size=(6, 1)) for i in range(1, 9)],
        wrap_width=640, key="-FLOW-")
    calendar = sg.TCalendar(key="-CAL-", enable_events=True)
    band_top = sg.Column([
        [sg.Column([[sg.TText("Frame")], [frame]]),
         sg.VerticalSeparator(),
         sg.Column([[sg.TText("Splitter（拖中间分隔条）")], [splitter]])],
    ])
    band_mid = sg.Column([
        [sg.Column([[sg.TText("ScrollableColumn（滚轮滚动）")], [scroll]]),
         sg.VerticalSeparator(),
         sg.Column([[sg.TText("Column（普通容器列）")],
                    [sg.TColumn([[sg.TText("内部元素一")],
                                [sg.TText("内部元素二")],
                                [sg.TButton("列内按钮")]])]]),
         sg.VerticalSeparator(),
         sg.Column([[sg.TText("Calendar（内嵌日历）")], [calendar]])],
    ])
    band_flow = sg.Column([
        [sg.TText("FlowPanel（拖拽窗口宽度看自动换行）")],
        [flow],
    ])
    return [[band_top], [band_mid], [band_flow]]


def tab_fancy():
    """战线 B 自绘控件页。"""
    return [
        [sg.Column([[sg.TText("RoundButton（Tk 画不出的圆角/圆形按钮）")],
                    [sg.TRoundButton("圆角按钮", size=(110, 30), radius=14,
                                     fill_color="#e91e63", key="-RB1-"),
                     sg.TRoundButton("圆形", size=(40, 40), radius=20,
                                     fill_color="#4caf50", key="-RB2-"),
                     sg.TRoundButton("深蓝", size=(110, 30), radius=8,
                                     fill_color="#3a7bd5", key="-RB3-")]])],
        [sg.Column([[sg.TText("ImageButton（整图点击）")],
                    [sg.TImageButton(data_base64=sg.DEFAULT_BASE64_ICON,
                                     key="-IB-"),
                     sg.TText("← 点这个 logo")]])],
        [sg.Column([[sg.TText("TextProgressBar（带百分比文字的进度条）")],
                    [sg.TTextProgressBar(100, current_value=60, size=(180, 22),
                                         bar_color="#4caf50", key="-TPB-"),
                     sg.TButton("+10", key="-B-TPB-ADD-"),
                     sg.TButton("清零", key="-B-TPB-ZERO-")]])],
    ]


def tab_system():
    return [
        [sg.Column([[sg.TText("弹窗家族")],
                    [sg.TButton("消息", key="-P-MSG-"), sg.TButton("Yes/No", key="-P-YN-"),
                     sg.TButton("错误", key="-P-ERR-"), sg.TButton("滚动文本", key="-P-SCROLL-"),
                     sg.TButton("输入框", key="-P-TEXT-"), sg.TButton("选文件", key="-P-FILE-"),
                     sg.TButton("选目录", key="-P-FOLDER-"), sg.TButton("选日期", key="-P-DATE-"),
                     sg.TButton("选字体", key="-P-FONT-")]])],
        [sg.Column([[sg.TText("窗口控制（QWidget 运行时 API）")],
                    [sg.TButton("居中", key="-W-CENTER-"), sg.TButton("最大化", key="-W-MAX-"),
                     sg.TButton("最小化", key="-W-MIN-"), sg.TButton("还原", key="-W-NORM-"),
                     sg.TButton("半透明", key="-W-ALPHA-"), sg.TButton("不透明", key="-W-ALPHA1-"),
                     sg.TButton("淡出淡入", key="-W-FADE-"), sg.TButton("滑走再滑回", key="-W-SLIDE-")]])],
        [sg.Column([[sg.TText("Toast 浮层 / 后台任务 / 定时器")],
                    [sg.TButton("Toast 通知", key="-W-TOAST-"),
                     sg.TButton("后台任务(2秒)", key="-W-WORK-"),
                     sg.TTextProgressBar(100, current_value=0, size=(20, 14),
                                         key="-PB-WORK-"),
                     sg.TButton("秒表开", key="-W-TIMER-"), sg.TButton("秒表关", key="-W-TIMEROFF-"),
                     sg.TText("00:00", key="-T-ELAPSED-", size=(8, 1))]])],
        [sg.Column([[sg.TText("系统集成")],
                    [sg.TButton("托盘：创建", key="-S-TRAY-"), sg.TButton("托盘：通知", key="-S-NOTIFY-"),
                     sg.TButton("托盘：关闭", key="-S-TRAYOFF-"),
                     sg.TButton("写剪贴板", key="-S-COPY-"), sg.TButton("读剪贴板", key="-S-PASTE-"),
                     sg.TButton("保存状态", key="-S-SAVE-"), sg.TButton("i18n 演示", key="-S-I18N-")],
                    [sg.TText("托盘图标出现后可左键/右键它；状态由 UserSettings 持久化。",
                             text_color="#888888")]])],
        [sg.Column([[sg.TText("窗口层级（parent）")],
                    [sg.TButton("打开子窗口", key="-W-CHILD-"),
                     sg.TText("子窗口在独立窗口里,主窗口关闭时级联关闭。",
                              text_color="#888888")]])],
    ]


# ---------------------------------------------------------------- 窗口组装 --
def build_actions():
    open_action = sg.Action("打开文件", key="-ACT-OPEN-", shortcut="<Control-o>")
    save_action = sg.Action("保存文件", key="-ACT-SAVE-", shortcut="<Control-s>")
    clear_action = sg.Action("清空日志", key="-ACT-CLEAR-")
    about_action = sg.Action("关于", key="-ACT-ABOUT-")
    return [open_action, save_action, clear_action, about_action]


def build_main_window():
    menu_def = [
        ["&文件", ["打开文件", "保存文件", "---", "退出"]],
        ["&主题", ["原生外观", "DarkBlue3 主题"]],
        ["&帮助", ["关于"]],
    ]
    toolbar = sg.TToolbar([
        ("新建", "-TOOL-NEW-"), ("打开文件", "-ACT-OPEN-"),
        ("保存文件", "-ACT-SAVE-"), "---", ("关于", "-ACT-ABOUT-"),
    ])
    tabs = sg.TTabGroup(
        [[sg.TTab("输入", tab_inputs()), sg.TTab("选择", tab_selection()),
          sg.TTab("数据", tab_data()), sg.TTab("绘图", tab_graphics()),
          sg.TTab("容器", tab_containers()), sg.TTab("炫彩", tab_fancy()),
          sg.TTab("系统", tab_system())]],
        key="-TABS-", enable_events=False, expand_x=True, expand_y=True)
    log_element = sg.TOutput(size=(96, 7), key="-LOG-", expand_x=True)
    log_element.right_click_menu = ["&日志", ["复制日志", "清空日志"]]
    layout = [
        [sg.TMenu(menu_def)],
        [toolbar],
        [tabs],
        [sg.TColumn([[sg.TText("事件日志（右键可复制/清空）")], [log_element]],
                    expand_x=True)],
        [sg.TStatusBar("", key="-STATUS-", expand_x=True), sg.TSizegrip()],
    ]
    window = sg.Window(
        "PySimpleGUI4 功能全景演示",
        layout,
        finalize=True,
        resizable=True,
        margins=(8, 6),
        actions=build_actions(),
        right_click_menu=["&窗口", ["清空日志", "关于"]],
    )
    _state["window"] = window
    _post_build(window)
    return window


def _post_build(window):
    # 树节点（带图标 + 分组 + 汇总行）
    tree = window["-TREE-"]
    tree.insert_group("", "grp-fruit", "水果组")
    tree.insert("grp-fruit", "apple", "苹果", image_data=ICON16)
    tree.insert_summary("grp-fruit", "sum-fruit", "1 项")
    tree.insert("", "standalone", "独立节点", image_data=ICON16)
    # Graph 初始图形
    graph = window["-GRAPH-"]
    graph.draw_circle((25, 40), 10, fill_color="#3a7bd5")
    graph.draw_line((0, 5), (100, 5), color="#cccccc")
    graph.draw_text("坐标 (50, 30)", (50, 30), color="#333333")
    # 状态栏：启动次数（UserSettings 持久化）
    count = (_PREFS.get("launches") or 0) + 1
    _PREFS.set("launches", count)
    _refresh_status()
    # 每秒刷新状态栏时钟（TTimer 对标）
    window.every(1000, _tick_clock)
    log(f"欢迎使用 PySimpleGUI4 {sg.__version__} —— 七个标签页 + window.run() 零循环")
    log("事件由 @app.bind_event 的 on_* 函数分发；Ctrl+O 打开、Ctrl+S 保存",
        color="#2e7d32")


def _refresh_status():
    window = _state["window"]
    count = _PREFS.get("launches") or 0
    window["-STATUS-"].update(
        f" 就绪 | {time.strftime('%H:%M:%S')} | 第 {count} 次启动 ")


def _tick_clock():
    window = _state["window"]
    if _STOPWATCH["start"] is not None:
        elapsed = int(time.time() - _STOPWATCH["start"])
        window["-T-ELAPSED-"].update(f"{elapsed // 60:02d}:{elapsed % 60:02d}")
    _refresh_status()


# ---------------------------------------------------------------- on_* 事件处理 --
# 全部通过 @app.bind_event 注册；签名支持 (window, values) 组合。

# 输入页
@app.bind_event("-IN-NUM-")
def on_num_input(window, values):
    log(f"整数校验输入: {values['-IN-NUM-']!r}")


@app.bind_event("-CB-SHOW-")
def on_show_password(window, values):
    window["-IN-PASS-"].set_password_char("" if values["-CB-SHOW-"] else "*")


@app.bind_event("-SP-")
def on_spin(window, values):
    log(f"Spin: {values['-SP-']}")


@app.bind_event("-SL-")
def on_slider(window, values):
    window["-PB-SL-"].update(current_value=values["-SL-"])


@app.bind_event("-B-COLOR-")
def on_color_print(window, values):
    ml = window["-ML-"]
    ml.print("信息：tk.Text 原生 tag 上色", text_color="#1565c0")
    ml.print("成功：一切正常", text_color="#2e7d32")
    ml.print("警告：这是黄色警告", text_color="#b8860b")
    ml.print("错误：这是红色错误", text_color="#c62828")


@app.bind_event(["-B-UNDO-"])
def on_undo(window, values):
    window["-ML-"].undo()


@app.bind_event(["-B-REDO-"])
def on_redo(window, values):
    window["-ML-"].redo()


@app.bind_event(["-B-CLEAR-ML-"])
def on_clear_ml(window, values):
    window["-ML-"].clear()


@app.bind_event("-B-FIND-")
def on_find(window, values):
    position = sg.popup_find(window["-ML-"])
    log(f"查找结果: {position}")


@app.bind_event("-B-REPLACE-")
def on_replace(window, values):
    count = sg.popup_replace(window["-ML-"])
    log(f"替换完成，共 {count} 处")


@app.bind_event("-SUBMIT-")
def on_submit(window, values):
    log(f"表单提交：用户名={values.get('-IN-USER-')!r} 数字={values.get('-IN-NUM-')!r}",
        color="#2e7d32")


# 选择页
@app.bind_event(["-CMB-", "-OPT-", "-SP2-", "-LB-", "-CBA-", "-CBB-",
                 "-CKL-", "-R1-", "-R2-", "-R3-"])
def on_selection(window, event, values):
    log(f"选择变化: {event} = {values.get(event)!r}")


@app.bind_event("-B-CKALL-")
def on_checklist_all(window, values):
    window["-CKL-"].check_all()
    log(f"勾选列表: {window['-CKL-'].get()}")


@app.bind_event("-B-CKNONE-")
def on_checklist_none(window, values):
    window["-CKL-"].uncheck_all()
    log(f"勾选列表: {window['-CKL-'].get()}")


# 数据页
@app.bind_event("-TB-")
def on_table_select(window, values):
    table = window["-TB-"]
    records = table.selected_records
    window["-T-REC-"].update(str(records[0]) if records else "")
    log(f"表格选中: {table.get()} 记录={records[0] if records else None}")


@app.bind_event("-B-REBIND-")
def on_rebind(window, values):
    window["-TB-"].bind([
        {"姓名": "新甲", "年龄": 21, "城市": "北京"},
        {"姓名": "新乙", "年龄": 33, "城市": "广州"},
    ])
    log("Table.bind 换数据完成（表头列自动同步）")


@app.bind_event("-B-ADDGRP-")
def on_tree_add_group(window, values):
    _state["tree_counter"] += 1
    key = f"grp-{_state['tree_counter']}"
    window["-TREE-"].insert_group("", key, f"分组 {_state['tree_counter']}")
    log(f"树插入分组: {key}")


@app.bind_event("-B-ADD-")
def on_tree_add(window, values):
    _state["tree_counter"] += 1
    name = f"节点 {_state['tree_counter']}"
    window["-TREE-"].insert("grp-fruit", f"n{_state['tree_counter']}",
                            name, image_data=ICON16)
    log(f"树插入: {name}")


@app.bind_event("-B-DEL-")
def on_tree_del(window, values):
    tree = window["-TREE-"]
    selection = tree.widget.selection()
    if selection:
        tree.widget.delete(*selection)
        log(f"树删除: {', '.join(str(s) for s in selection)}")
    else:
        sg.popup_notify("请先选中一个节点")


@app.bind_event("-B-KVGET-")
def on_kv_get(window, values):
    log(f"KeyValueEditor: {window['-KV-'].get()}")


# 绘图页
@app.bind_event("-GRAPH-")
def on_graph_click(window, values):
    graph = window["-GRAPH-"]
    log(f"画布点击，当前图元 {len(graph.widget.find_all())} 个")


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
        figure_id = graph.draw_text("字", (x, 15), color="#1565c0")
    _state["figure_last"] = figure_id
    log(f"绘制 {kind} -> 图元 id {figure_id}")


@app.bind_event("-B-CIRCLE-")
def on_draw_circle(window, values):
    _draw("circle", window)


@app.bind_event("-B-RECT-")
def on_draw_rect(window, values):
    _draw("rect", window)


@app.bind_event("-B-TEXT-")
def on_draw_text(window, values):
    _draw("text", window)


@app.bind_event("-B-MOVEF-")
def on_move_figure(window, values):
    figure = _state["figure_last"]
    if figure is not None:
        window["-GRAPH-"].move_figure(figure, 3, 2)
        log(f"移动图元 id {figure}")


@app.bind_event("-B-DELF-")
def on_delete_figure(window, values):
    figure = _state["figure_last"]
    if figure is not None:
        window["-GRAPH-"].delete_figure(figure)
        log(f"删除图元 id {figure}")
        _state["figure_last"] = None


@app.bind_event("-B-CLEARG-")
def on_clear_graph(window, values):
    window["-GRAPH-"].erase()
    _state["figure_last"] = None
    log("画布已清空")


@app.bind_event("-CAL-")
def on_calendar(window, values):
    log(f"日历选择: {values['-CAL-']}")


# 炫彩页（战线 B 自绘控件）
@app.bind_event(["-RB1-", "-RB2-", "-RB3-"])
def on_round_button(window, event, values):
    log(f"RoundButton 点击: {event}")


@app.bind_event("-IB-")
def on_image_button(window, values):
    log("ImageButton 点击（整图都是点击区）")


@app.bind_event("-B-TPB-ADD-")
def on_tpb_add(window, values):
    bar = window["-TPB-"]
    bar.update(current_value=min(bar.max_value, bar.get() + 10))
    log(f"TextProgressBar: {bar.get()}%")


@app.bind_event("-B-TPB-ZERO-")
def on_tpb_zero(window, values):
    window["-TPB-"].update(current_value=0)
    log("TextProgressBar 清零")


# 弹窗家族
@app.bind_event("-P-MSG-")
def on_p_msg(window, values):
    log(f"popup 返回: {sg.popup('这是 popup 消息')!r}")


@app.bind_event("-P-YN-")
def on_p_yn(window, values):
    log(f"popup_yes_no 返回: {sg.popup_yes_no('确定继续？')!r}")


@app.bind_event("-P-ERR-")
def on_p_err(window, values):
    sg.popup_error("出错了（演示）")


@app.bind_event("-P-SCROLL-")
def on_p_scroll(window, values):
    sg.popup_scrolled(
        "\n".join(f"第 {i} 行内容" for i in range(1, 21)),
        title="滚动文本")


@app.bind_event("-P-TEXT-")
def on_p_text(window, values):
    log(f"popup_get_text 返回: {sg.popup_get_text('请输入一句话')!r}")


@app.bind_event("-P-FILE-")
def on_p_file(window, values):
    log(f"选择的文件: {sg.popup_get_file('选个文件')!r}")


@app.bind_event("-P-FOLDER-")
def on_p_folder(window, values):
    log(f"选择的目录: {sg.popup_get_folder('选个目录')!r}")


@app.bind_event("-P-DATE-")
def on_p_date(window, values):
    log(f"选择的日期: {sg.popup_get_date()}")


@app.bind_event("-P-FONT-")
def on_p_font(window, values):
    log(f"选择的字体: {sg.popup_get_font(include_bold_italic=True)}")


# 窗口控制
@app.bind_event("-W-CENTER-")
def on_w_center(window, values):
    window.move_to_center()


@app.bind_event("-W-MAX-")
def on_w_max(window, values):
    window.maximize()


@app.bind_event("-W-MIN-")
def on_w_min(window, values):
    window.minimize()


@app.bind_event("-W-NORM-")
def on_w_norm(window, values):
    window.normal()


@app.bind_event("-W-ALPHA-")
def on_w_alpha(window, values):
    window.set_alpha_channel(0.5)


@app.bind_event("-W-ALPHA1-")
def on_w_alpha1(window, values):
    window.set_alpha_channel(1.0)


@app.bind_event("-W-FADE-")
def on_w_fade(window, values):
    sg.fade_out(window, duration_ms=400, steps=8,
                on_done=lambda: window.after(
                    150, lambda: sg.fade_in(window, duration_ms=400, steps=8)))
    log("淡出→淡入（after 链）")


@app.bind_event("-W-SLIDE-")
def on_w_slide(window, values):
    start = window.current_location()
    sg.slide(window, (start[0] + 120, start[1]), duration_ms=400, steps=8,
             on_done=lambda: sg.slide(window, start, duration_ms=400, steps=8))


@app.bind_event("-W-TOAST-")
def on_w_toast(window, values):
    window.toast("操作已保存", title="Toast", duration_ms=2500)
    log("Toast 浮层已显示（右下角淡入淡出）")


@app.bind_event("-W-WORK-")
def on_w_work(window, values):
    sg.animate_progress(window, "-PB-WORK-", 100,
                        duration_ms=1800, steps=18,
                        on_done=lambda: window["-PB-WORK-"].update(current_value=0))
    window.perform_long_operation(
        lambda: (time.sleep(2), "后台任务完成")[1], end_key="-WORK-DONE-")
    log("后台线程已启动（期间界面可正常操作）")


@app.bind_event("-WORK-DONE-")
def on_work_done(window, values):
    log("perform_long_operation 返回 -WORK-DONE-", color="#2e7d32")


@app.bind_event("-W-TIMER-")
def on_timer_on(window, values):
    _STOPWATCH["start"] = time.time()
    log("秒表已启动")


@app.bind_event("-W-TIMEROFF-")
def on_timer_off(window, values):
    _STOPWATCH["start"] = None
    window["-T-ELAPSED-"].update("00:00")
    log("秒表已停止")


# 窗口层级：在 parent= 的子窗口里放一个会发事件的按钮
@app.bind_event("-W-CHILD-")
def on_w_child(window, values):
    if _state["about_window"] is not None and not _state["about_window"].was_closed:
        _state["about_window"].bring_to_front()
        return
    child_layout = [
        [sg.TText("这是 parent=主窗口 的子窗口")],
        [sg.TText("层级: child.parent == 主窗口, 主窗口.children 含本窗口")],
        [sg.TButton("子窗口里点我", key="-CHILD-PING-")],
        [sg.TButton("关闭子窗口", key="-CHILD-CLOSE-")],
    ]
    _state["about_window"] = sg.Window(
        "子窗口演示", child_layout, finalize=True, parent=window)
    log("子窗口已打开（主窗口关闭时会级联关闭）", color="#2e7d32")


@app.bind_event("-CHILD-PING-")
def on_child_ping(window, values):
    # window 参数是事件所属窗口——这里可能是子窗口也可能被主循环读到
    log(f"子窗口按钮点击（来自 {window.title}）")


@app.bind_event("-CHILD-CLOSE-")
def on_child_close(window, values):
    if _state["about_window"] is not None:
        _state["about_window"].close()
        _state["about_window"] = None
    log("子窗口已关闭")


# 系统集成
@app.bind_event("-S-TRAY-")
def on_tray_create(window, values):
    if _TRAY["obj"] is not None:
        sg.popup_notify("托盘已存在")
        return
    try:
        _TRAY["obj"] = sg.SystemTray(title="PySimpleGUI4 演示",
                                     menu=["显示通知", "退出托盘"])
        log("托盘图标已创建（左键/右键它有事件与菜单）", color="#2e7d32")
    except RuntimeError as error:
        sg.popup_error(str(error))


@app.bind_event("-S-NOTIFY-")
def on_tray_notify(window, values):
    if _TRAY["obj"] is not None:
        _TRAY["obj"].ShowMessage("PySimpleGUI4", "这是托盘气泡通知")
    else:
        sg.popup_notify("先创建托盘")


@app.bind_event("-S-TRAYOFF-")
def on_tray_off(window, values):
    if _TRAY["obj"] is not None:
        _TRAY["obj"].close()
        _TRAY["obj"] = None
        log("托盘已关闭")


@app.bind_event("-S-COPY-")
def on_copy(window, values):
    window.clipboard_set(f"PySimpleGUI4 剪贴板演示 {time.time()}")
    log("已写入剪贴板")


@app.bind_event("-S-PASTE-")
def on_paste(window, values):
    log(f"剪贴板内容: {window.clipboard_get()!r}")


@app.bind_event("-S-SAVE-")
def on_save_state(window, values):
    _PREFS.set("last_theme", sg.theme())
    _PREFS.set("last_seen", time.strftime("%Y-%m-%d %H:%M:%S"))
    log(f"UserSettings 已保存: last_theme={_PREFS.get('last_theme')!r}, "
        f"last_seen={_PREFS.get('last_seen')}")


@app.bind_event("-S-I18N-")
def on_i18n(window, values):
    sg.set_translations({"Open": "打开", "Save": "保存"})
    sample = [sg._("Open"), sg._("Save"), sg._("Unknown stays")]
    log(f"i18n: {' / '.join(sample)}")
    sg.clear_translations()


# 菜单/工具栏/右键共享
@app.bind_event("-ACT-OPEN-")
def on_open(window, values):
    path = sg.popup_get_file("打开（Ctrl+O）")
    log(f"Action 打开文件: {path!r}")


@app.bind_event("-ACT-SAVE-")
def on_save(window, values):
    path = sg.popup_get_file("保存（Ctrl+S）", save_as=True)
    log(f"Action 保存文件: {path!r}")


@app.bind_event("-ACT-CLEAR-")
def on_clear_log(window, values):
    window["-LOG-"].clear()
    log("日志已清空")


@app.bind_event("-ACT-ABOUT-")
def on_about(window, values):
    sg.popup_ok(
        f"PySimpleGUI4 {sg.__version__}\n\nOO 重写的 PySimpleGUI 4.x 分支\n"
        "零依赖 / Python 3.7+ / 原生默认外观",
        title="关于")


@app.bind_event("复制日志")
def on_copy_log(window, values):
    window.clipboard_set(window["-LOG-"].get())
    sg.popup_notify("日志已复制到剪贴板")


@app.bind_event(["原生外观", "DarkBlue3 主题"])
def on_theme(window, event, values):
    if event == "DarkBlue3 主题":
        name = sg.theme("DarkBlue3")
    else:
        name = sg.theme(None)
    log(f"主题已切换为 {name}（对新建窗口生效，重开演示可见）", color="#1565c0")


@app.bind_event("-TOOL-NEW-")
def on_tool_new(window, values):
    log("工具栏: 新建")


@app.bind_event("退出")
def on_exit(window, values):
    if _TRAY["obj"] is not None:
        _TRAY["obj"].close()
        _TRAY["obj"] = None
    sg.Window.close_all()


# ---------------------------------------------------------------- 入口 --
def main(argv=None):
    sg.set_dpi_awareness()  # Windows 高分屏清晰渲染（进程级，一次即可）
    smoke = "--smoke" in (argv or sys.argv[1:])
    window = build_main_window()
    try:
        if smoke:
            # 自检：直接调用若干 handler 验证接线（无弹窗路径）
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
        # 用户零循环：window.run() 启动应用（on_* 函数已注册在 default_app 上）
        window.run()
    finally:
        if _TRAY["obj"] is not None:
            _TRAY["obj"].close()
        sg.Window.close_all()
    return 0


if __name__ == "__main__":
    sys.exit(main())
