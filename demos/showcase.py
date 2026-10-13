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

Note: all user-facing strings are Chinese (menu labels double as event
names, so handlers bind the same Chinese literals).
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

# menu label -> theme identifier (menu labels double as event names)
_THEME_MENU_LABELS = {
    "系统（原生）": "System",
    "板岩": "Slate",
    "日光": "Daylight",
    "暮色": "Dusk",
    "鼠尾草": "Sage",
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
        [ts.Column([[ts.TText("整数校验（仅允许数字）")],
                    [ts.TInput("", key="-IN-NUM-", size=(12, 1), validate="key",
                              validate_command=ts.validate_integer,
                              enable_events=True)]]),
         ts.Column([[ts.TText("密码框")],
                    [ts.TInput("", key="-IN-PASS-", size=(12, 1), password_char="*")],
                    [ts.TCheckbox("显示密码", key="-CB-SHOW-", enable_events=True)]]),
         ts.Column([[ts.TLabeledEdit("用户名", "yunluo", key="-IN-USER-")],
                    [ts.TButton("提交表单", key="-SUBMIT-")]]),
         ts.Column([[ts.TText("微调框")],
                    [ts.TSpin([str(n) for n in range(1, 11)], initial_value="5",
                              key="-SP-", enable_events=True)]])],
    ])
    band_slider = ts.Column([
        [ts.TText("滑杆联动进度条（拖动时显示数值气泡）：")],
        [ts.TSlider((0, 100), default_value=30, key="-SL-",
                    enable_events=True, size=(18, 15), show_value=True),
         ts.TProgressBar(100, current_value=30, size=(20, 12), key="-PB-SL-")],
    ])
    band_multiline = ts.Column([
        [ts.TMultiline("多行文本区（撤销/重做、彩色输出、查找替换）\n",
                       key="-ML-", size=(56, 5))],
        [ts.TButton("彩色输出", key="-B-COLOR-"), ts.TButton("撤销", key="-B-UNDO-"),
         ts.TButton("重做", key="-B-REDO-"), ts.TButton("查找", key="-B-FIND-"),
         ts.TButton("替换", key="-B-REPLACE-"), ts.TButton("清空", key="-B-CLEAR-ML-")],
    ])
    return [[band_top], [band_slider], [band_multiline]]


def tab_selection():
    band = ts.Column([
        [ts.Column([[ts.TText("下拉框")],
                    [ts.TCombo(["红色", "绿色", "蓝色"], default_value="红色",
                              key="-CMB-", enable_events=True)],
                    [ts.TText("选项菜单")],
                    [ts.TOptionMenu(["第一项", "第二项", "第三项"], key="-OPT-",
                                   enable_events=True)],
                    [ts.TText("微调框")],
                    [ts.TSpin(["低", "中", "高"], initial_value="中",
                             key="-SP2-", enable_events=True)]],
                   ),
         ts.Column([[ts.TText("列表框（多选）")],
                    [ts.TListbox(["选项一", "选项二", "选项三", "选项四"],
                                size=(14, 4), select_mode=ts.SelectMode.EXTENDED,
                                key="-LB-", enable_events=True)]]),
         ts.Column([[ts.TText("复选框")],
                    [ts.TCheckbox("勾选 A", key="-CBA-", enable_events=True)],
                    [ts.TCheckbox("勾选 B", key="-CBB-", enable_events=True)]]),
         ts.Column([[ts.TText("复选列表")],
                    [ts.TCheckList(["西瓜", "苹果", "香蕉"],
                                  default_checked=["苹果"], key="-CKL-",
                                  enable_events=True)],
                    [ts.TButton("全选", key="-B-CKALL-"),
                     ts.TButton("全不选", key="-B-CKNONE-")]]),
         ts.Column([[ts.TText("单选（互斥）")],
                    [ts.TRadio("方案一", "plan", default=True, key="-R1-",
                              enable_events=True)],
                    [ts.TRadio("方案二", "plan", key="-R2-", enable_events=True)],
                    [ts.TRadio("方案三", "plan", key="-R3-", enable_events=True)]])],
    ])
    return [[band]]


def tab_data():
    records = [
        {"姓名": "云落", "年龄": 30, "城市": "深圳"},
        {"姓名": "小明", "年龄": 24, "城市": "杭州"},
        {"姓名": "阿强", "年龄": 36, "城市": "成都"},
        {"姓名": "小美", "年龄": 28, "城市": "上海"},
    ]
    table = ts.TTable([], headings=[], key="-TB-", enable_edit=True,
                      row_icons=[ICON16, ICON16, ICON16, ICON16], num_rows=5,
                      auto_size_columns=False, col_widths=[10, 8, 10])
    table.bind(records)
    tree = ts.TTree(headings=["节点"], show_headings=False, num_rows=6, key="-TREE-")
    kv = ts.TKeyValueEditor([("主机", "localhost"), ("端口", "5432")], key="-KV-")
    band = ts.Column([
        [ts.Column([[ts.TText("表格：点表头排序 / 双击编辑 / 行图标 / 拖动分隔线")],
                    [table],
                    [ts.TButton("重新绑定数据", key="-B-REBIND-"),
                     ts.TText("当前记录："),
                     ts.TText("", key="-T-REC-", size=(22, 1))]]),
         ts.Column([[ts.TText("树（图标 / 分组 / 汇总行）")],
                    [tree],
                    [ts.TButton("添加分组", key="-B-ADDGRP-"),
                     ts.TButton("添加节点", key="-B-ADD-"),
                     ts.TButton("删除节点", key="-B-DEL-")]]),
         ts.Column([[ts.TText("键值编辑器（TValEdit）")],
                    [kv],
                    [ts.TButton("读取数值", key="-B-KVGET-")]])],
    ])
    return [[band]]


def tab_graphics():
    graph = ts.TGraph((320, 160), (0, 0), (100, 54), key="-GRAPH-",
                      enable_events=True, background_color="#ffffff")
    # --- TChart gallery: every chart type on one page ------------------------
    charts = {}
    specs = [
        ("-CH-LINE-", "line", "折线图", "营收", "right"),
        ("-CH-BAR-", "bar", "柱状图", "销量", "bottom"),
        ("-CH-AREA-", "area", "面积图", "趋势", "top"),
        ("-CH-SCATTER-", "scatter", "散点图（误差棒）", "采样", "right"),
        ("-CH-HBAR-", "hbar", "横向条形图", "速度", "left"),
        ("-CH-PIE-", "pie", "饼图", "份额", "bottom"),
        ("-CH-DONUT-", "donut", "环形图", "占比", "right"),
        ("-CH-STACKED-", "stacked", "堆叠柱状图", "总量", "bottom"),
        ("-CH-HISTO-", "histogram", "直方图", "分布", "top"),
    ]
    for key, kind, _label, title, legend_pos in specs:
        smooth = key == "-CH-LINE-"
        # the line chart carries SPC-style control limits (reference lines)
        hlines = [(35, "目标 35"), (10, "下限 10", "#c62828")] \
            if key == "-CH-LINE-" else None
        chart = ts.TChart((300, 190), chart_type=kind, title=title,
                          legend=(kind not in ("pie", "donut")),
                          legend_position=legend_pos, key=key,
                          enable_events=True, smooth=smooth, hlines=hlines,
                          bins=8 if kind == "histogram" else None)
        charts[key] = chart
    charts["-CH-LINE-"].add_series("2024", [12, 34, 28, 41, 26, 38],
                                   labels=["一月", "二月", "三月", "四月", "五月", "六月"])
    charts["-CH-LINE-"].add_series("2025", [22, 30, 38, 35, 31, 44])
    charts["-CH-BAR-"].add_series("东部", [12, 30, 8, 24],
                                  labels=["一季度", "二季度", "三季度", "四季度"])
    charts["-CH-BAR-"].add_series("西部", [9, 24, 16, 20])
    charts["-CH-AREA-"].add_series("负载", [4, 6, 5, 9, 7, 11, 8])
    charts["-CH-SCATTER-"].add_series(
        "样本", [1, 5, 3, 8, 2, 7, 4, 9],
        errors=[0.4, 0.9, 0.5, 1.2, 0.3, 0.8, 0.6, 1.0])
    charts["-CH-HBAR-"].add_series("速度", [40, 65, 30, 80],
                                   labels=["甲", "乙", "丙", "丁"])
    charts["-CH-PIE-"].add_series("份额",
                                  [("甲", 30), ("乙", 20), ("丙", 15), ("丁", 35)])
    charts["-CH-DONUT-"].add_series("占比",
                                    [("甲", 45), ("乙", 25), ("丙", 30)])
    charts["-CH-STACKED-"].add_series("线上", [10, 16, 12, 20],
                                      labels=["一季度", "二季度", "三季度", "四季度"])
    charts["-CH-STACKED-"].add_series("线下", [8, 6, 11, 7])
    charts["-CH-HISTO-"].add_series("测量值", [
        38.2, 39.1, 41.3, 40.2, 37.8, 42.1, 39.9, 40.8, 38.6, 41.7,
        40.1, 39.3, 42.6, 38.9, 40.5, 41.1, 39.7, 40.4, 43.2, 37.2,
        41.9, 40.0, 39.5, 42.8, 38.4, 40.9, 41.5, 39.2, 40.6, 42.3,
    ])
    for chart in charts.values():
        chart.redraw()
    return [
        [ts.Column([[ts.TText("TChart 图表 -- 折线（含控制限）/ 柱状 / 面积 / 散点（误差棒）"
                              " / 横条 / 饼图 / 环形 / 堆叠 / 直方图")],
                    [ts.TButton("更新折线数据", key="-B-CHUPD-"),
                     ts.TButton("添加柱状系列", key="-B-CHADD-"),
                     ts.TButton("重掷饼图", key="-B-CHPIE-")],
                    [charts["-CH-LINE-"], charts["-CH-BAR-"],
                     charts["-CH-AREA-"]],
                    [charts["-CH-SCATTER-"], charts["-CH-HBAR-"],
                     charts["-CH-PIE-"]],
                    [charts["-CH-DONUT-"], charts["-CH-STACKED-"],
                     charts["-CH-HISTO-"]]])],
        [ts.Column([[ts.TText("TGraph 自由绘图（用户坐标 + 图元句柄）-- 点击画布试试")],
                    [graph],
                    [ts.TButton("画圆", key="-B-CIRCLE-"),
                     ts.TButton("画矩形", key="-B-RECT-"),
                     ts.TButton("画文字", key="-B-TEXT-"),
                     ts.TButton("移动图元", key="-B-MOVEF-"),
                     ts.TButton("删除最后", key="-B-DELF-"),
                     ts.TButton("清空", key="-B-CLEARG-")]])],
        [ts.Column([[ts.TText("形状 / 画布 / 图像")],
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
    frame = ts.TFrame("分组框架", [[ts.TInput("框架内文本", key="-IN-FRAME-")]],
                      key="-FRAME-")
    splitter = ts.TSplitter(
        [[[ts.TText("左侧面板")], [ts.TListbox(["甲", "乙", "丙"], size=(9, 3))]],
         [[ts.TText("右侧面板（拖动分隔条）")], [ts.TInput("拖我", size=(18, 1))]]],
        key="-SPLIT-")
    scroll = ts.TScrollableColumn(
        [[ts.TText(f"  滚动行 {i:>2d} ")] for i in range(1, 21)],
        size=(140, 110), key="-SCROLL-", background_color="#f7f7f7")
    flow = ts.TFlowPanel(
        [ts.TButton(f"按钮 {i}", size=(6, 1)) for i in range(1, 9)],
        wrap_width=640, key="-FLOW-")
    calendar = ts.TCalendar(key="-CAL-", enable_events=True)
    band_top = ts.Column([
        [ts.Column([[ts.TText("框架 Frame")], [frame]]),
         ts.VerticalSeparator(),
         ts.Column([[ts.TText("分栏 Splitter（拖动中间分隔条）")], [splitter]])],
    ])
    band_mid = ts.Column([
        [ts.Column([[ts.TText("滚动容器（滚轮滚动）")], [scroll]]),
         ts.VerticalSeparator(),
         ts.Column([[ts.TText("普通容器 Column")],
                    [ts.TColumn([[ts.TText("内部元素一")],
                                [ts.TText("内部元素二")],
                                [ts.TButton("容器内按钮")]])]]),
         ts.VerticalSeparator(),
         ts.Column([[ts.TText("日历（内嵌）")], [calendar]])],
    ])
    band_flow = ts.Column([
        [ts.TText("流式面板 FlowPanel（缩放窗口查看自动换行）")],
        [flow],
    ])
    return [[band_top], [band_mid], [band_flow]]


def tab_fancy():
    """Canvas-drawn widgets page."""
    gauge = ts.TGauge(100, value=72, size=(150, 118), units="%",
                      title="储罐液位", key="-GAUGE-")
    alarm_gauge = ts.TGauge(60, value=64, min_value=-20, size=(150, 118),
                            title="温度 °C", key="-GAUGE2-")
    return [
        [ts.Column([[ts.TText("圆角按钮（Tk 画不出的圆角/圆形按钮）")],
                    [ts.TRoundButton("圆角按钮", size=(110, 30), radius=14,
                                     fill_color="#e91e63", key="-RB1-"),
                     ts.TRoundButton("圆", size=(40, 40), radius=20,
                                     fill_color="#4caf50", key="-RB2-"),
                     ts.TRoundButton("深蓝按钮", size=(110, 30), radius=8,
                                     fill_color="#3a7bd5", key="-RB3-")]])],
        [ts.Column([[ts.TText("图像按钮（整张图片都是点击区）")],
                    [ts.TImageButton(data_base64=ts.DEFAULT_BASE64_ICON,
                                     key="-IB-"),
                     ts.TText("<- 点击这个徽标")]])],
        [ts.Column([[ts.TText("文字进度条（带百分比文字）")],
                    [ts.TTextProgressBar(100, current_value=60, size=(180, 22),
                                         bar_color="#4caf50", key="-TPB-"),
                     ts.TButton("+10", key="-B-TPB-ADD-"),
                     ts.TButton("归零", key="-B-TPB-ZERO-")]])],
        [ts.Column([[ts.TText("仪表盘 Gauge（工业 HMI：报警色带 + 指针 + 数字读数）"
                             "-- 拖动滑杆联动")],
                    [gauge, alarm_gauge,
                     ts.Column([[ts.TSlider((0, 100), default_value=72,
                                            key="-SL-GAUGE-", enable_events=True,
                                            size=(14, 12))],
                                [ts.TButton("模拟波动", key="-B-GAUGE-RND-")]]),
                     ts.VerticalSeparator(),
                     ts.TText("绿 / 黄 / 红报警带自动按量程分布；"
                              "读数超上限时指针停在最大值。", text_color="#888888")]])],
    ]


def tab_themes():
    """A visual swatch + preview for each of the five built-in themes.

    Clicking a swatch row opens a sample window in that theme; the
    ``设为默认`` button switches the global theme for every future window.
    """
    from TkSimpleGUI._theme_data import LOOK_AND_FEEL_TABLE

    descriptions = {
        "System": "原生 / 默认 / 平台观感",
        "Slate": "深色 / 专业 / 工业 / 冷色",
        "Daylight": "浅色 / 办公 / 素净 / 现代",
        "Dusk": "深色 / 暖调 / 夜晚 / 舒适",
        "Sage": "浅色 / 自然 / 平静 / 清新",
    }
    rows = []
    rows.append([ts.TText(
        "点击主题行打开该配色示例窗口，或设为新建窗口的默认主题。"
        "五套手工挑选的低饱和配色，商用与个人应用皆宜。"
    )])
    for name in ("System", "Slate", "Daylight", "Dusk", "Sage"):
        palette = LOOK_AND_FEEL_TABLE[name]["COLOR_LIST"]
        bg, accent, panel, fg = palette
        # System uses sentinel "system" placeholders -- resolve to a
        # neutral sample swatch so the row still shows something
        sample = ["#cfd2d6" if c == "system" else c for c in (bg, accent, panel, fg)]
        swatch = ts.TCanvas((180, 40), key=f"-SW-{name}-", background_color=sample[0])
        row = ts.Column([
            [ts.TText(f"{name:9s}", size=(10, 1),
                      font=("Segoe UI", 10, "bold"), key=f"-LBL-{name}-"),
             swatch,
             ts.TText(descriptions[name], size=(38, 1), text_color="#666666",
                      key=f"-DESC-{name}-"),
             ts.TButton("预览", key=f"-PREVIEW-{name}-"),
             ts.TButton("设为默认", key=f"-SET-{name}-")]
        ], key=f"-ROW-{name}-", pad=(2, 2))
        rows.append([row])
    return rows


def tab_system():
    return [
        [ts.Column([[ts.TText("弹窗家族")],
                    [ts.TButton("消息", key="-P-MSG-"), ts.TButton("是否", key="-P-YN-"),
                     ts.TButton("错误", key="-P-ERR-"),
                             ts.TButton("滚动文本", key="-P-SCROLL-"),
                     ts.TButton("输入", key="-P-TEXT-"), ts.TButton("文件", key="-P-FILE-"),
                     ts.TButton("文件夹", key="-P-FOLDER-"), ts.TButton("日期", key="-P-DATE-"),
                     ts.TButton("字体", key="-P-FONT-")]])],
        [ts.Column([[ts.TText("窗口控制（运行时 API）")],
                    [ts.TButton("居中", key="-W-CENTER-"), ts.TButton("最大化", key="-W-MAX-"),
                     ts.TButton("最小化", key="-W-MIN-"), ts.TButton("还原", key="-W-NORM-"),
                     ts.TButton("半透明 0.6", key="-W-ALPHA-"),
                             ts.TButton("半透明 1.0", key="-W-ALPHA1-"),
                     ts.TButton("淡出淡入", key="-W-FADE-"),
                             ts.TButton("滑出滑回", key="-W-SLIDE-")]])],
        [ts.Column([[ts.TText("Toast 气泡 / 后台任务 / 定时器")],
                    [ts.TButton("Toast 气泡", key="-W-TOAST-"),
                     ts.TButton("后台任务（2 秒）", key="-W-WORK-"),
                     ts.TTextProgressBar(100, current_value=0, size=(20, 14),
                                         key="-PB-WORK-"),
                     ts.TButton("计时开", key="-W-TIMER-"),
                             ts.TButton("计时关", key="-W-TIMEROFF-"),
                     ts.TText("00:00", key="-T-ELAPSED-", size=(8, 1))]])],
        [ts.Column([[ts.TText("LED 数码管（七段显示）")],
                    [ts.TLED(0, digits=6, color="#ff3b30", key="-LED-COUNT-"),
                     ts.VerticalSeparator(),
                     ts.TLED("00:00", digits=5, allow_colon=True,
                             color="#33cc66", key="-LED-CLOCK-"),
                     ts.VerticalSeparator(),
                     ts.TLED(-3.14, digits=6, color="#33aaff", key="-LED-NEG-")]])],
        [ts.Column([[ts.TText("系统集成")],
                    [ts.TButton("托盘：创建", key="-S-TRAY-"),
                            ts.TButton("托盘：通知", key="-S-NOTIFY-"),
                     ts.TButton("托盘：关闭", key="-S-TRAYOFF-"),
                     ts.TButton("写剪贴板", key="-S-COPY-"),
                             ts.TButton("读剪贴板", key="-S-PASTE-"),
                     ts.TButton("保存偏好", key="-S-SAVE-"),
                             ts.TButton("i18n 演示", key="-S-I18N-")],
                    [ts.TText("左/右键点击托盘图标；偏好通过 UserSettings 持久化。",
                             text_color="#888888")]])],
        [ts.Column([[ts.TText("窗口层级（parent）")],
                    [ts.TButton("打开子窗口", key="-W-CHILD-"),
                     ts.TText("子窗口独立存在；关闭主窗口时级联关闭。",
                              text_color="#888888")]])],
    ]


# ---------------------------------------------------------------- window assembly --
def build_actions():
    open_action = ts.Action("打开文件", key="-ACT-OPEN-", shortcut="<Control-o>")
    save_action = ts.Action("保存文件", key="-ACT-SAVE-", shortcut="<Control-s>")
    clear_action = ts.Action("清空日志", key="-ACT-CLEAR-")
    about_action = ts.Action("关于", key="-ACT-ABOUT-")
    return [open_action, save_action, clear_action, about_action]


def build_main_window():
    menu_def = [
        ["文件(&F)", ["打开文件", "保存文件", "---", "退出"]],
        ["主题(&T)", list(_THEME_MENU_LABELS)],
        ["帮助(&H)", ["关于"]],
    ]
    toolbar = ts.TToolbar([
        ("新建", "-TOOL-NEW-"), ("打开文件", "-ACT-OPEN-"),
        ("保存文件", "-ACT-SAVE-"), "---", ("关于", "-ACT-ABOUT-"),
    ])
    tabs = ts.TTabGroup(
        [[ts.TTab("输入控件", tab_inputs()), ts.TTab("选择控件", tab_selection()),
          ts.TTab("数据展示", tab_data()), ts.TTab("图形图表", tab_graphics()),
          ts.TTab("容器", tab_containers()), ts.TTab("趣味控件", tab_fancy()),
          ts.TTab("主题", tab_themes()),
          ts.TTab("系统", tab_system())]],
        key="-TABS-", enable_events=False, expand_x=True, expand_y=True)
    log_element = ts.TOutput(size=(96, 7), key="-LOG-", expand_x=True)
    log_element.right_click_menu = ["日志", ["复制日志", "清空日志"]]
    layout = [
        [ts.TMenu(menu_def)],
        [toolbar],
        [tabs],
        [ts.TColumn([[ts.TText("事件日志（右键复制/清空）")], [log_element]],
                    expand_x=True)],
        [ts.TStatusBar("", key="-STATUS-", expand_x=True), ts.TSizegrip()],
    ]
    window = ts.Window(
        "TkSimpleGUI 功能展示",
        layout,
        finalize=True,
        resizable=True,
        margins=(8, 6),
        actions=build_actions(),
        right_click_menu=["窗口", ["清空日志", "关于"]],
        on_close=_confirm_exit,
    )
    _state["window"] = window
    _post_build(window)
    return window


def _confirm_exit(window):
    """The main window's title bar X asks before quitting.

    Returning True lets the close proceed (and tear down the app loop);
    False keeps the window open. The hard-quit path stays 文件 > 退出.
    """
    answer = ts.popup_yes_no(
        "确定退出 TkSimpleGUI 功能展示吗？",
        title="退出",
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
        [ts.TText(f"预览 -- {theme_name} 主题", font=("Segoe UI", 10, "bold"))],
        [ts.TText("本主题下的标签 / TText")],
        [ts.TInput("输入框（TInput）", key="-PREV-IN-")],
        [ts.TCheckbox("复选框选项", key="-PREV-CB-"),
         ts.TRadio("单选 A", "g", key="-PREV-R1-", default=True),
         ts.TRadio("单选 B", "g", key="-PREV-R2-")],
        [ts.TButton("主要操作"), ts.TButton("次要操作"),
         ts.TButton("取消")],
        [ts.TProgressBar(100, current_value=42, size=(220, 14),
                         key="-PREV-PB-")],
        [ts.TStatusBar(f"主题：{theme_name}", size=(30, 1))],
    ]
    try:
        ts.Window(f"预览 -- {theme_name}", layout,
                  finalize=True, modal=True, resizable=False)
        log(f"已打开 {theme_name} 主题预览窗口", color="#1565c0")
    finally:
        # revert so the rest of the app keeps the user's chosen theme
        ts.theme(previous)


def _post_build(window):
    # theme swatches on the Themes tab
    _draw_theme_swatches(window)
    # tree nodes (icons + groups + summary rows)
    tree = window["-TREE-"]
    tree.insert_group("", "grp-fruit", "水果分组")
    tree.insert("grp-fruit", "apple", "苹果", image_data=ICON16)
    tree.insert_summary("grp-fruit", "sum-fruit", "共 1 项")
    tree.insert("", "standalone", "独立节点", image_data=ICON16)
    # initial graph figures
    graph = window["-GRAPH-"]
    graph.draw_circle((25, 40), 10, fill_color="#3a7bd5")
    graph.draw_line((0, 5), (100, 5), color="#cccccc")
    graph.draw_text("坐标 (50, 30)", (50, 30), color="#333333")
    # status bar: launch counter (persisted via UserSettings)
    count = (_PREFS.get("launches") or 0) + 1
    _PREFS.set("launches", count)
    _refresh_status()
    # refresh the status bar clock every second
    window.every(1000, _tick_clock)
    log(f"欢迎使用 TkSimpleGUI {ts.__version__} -- 八个页签，零事件循环")
    log("事件经 @ts.bind_event 分发到 on_* 函数；Ctrl+O 打开、Ctrl+S 保存",
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
        window["-LED-CLOCK-"].update(f"{elapsed // 60:02d}:{elapsed % 60:02d}")
        window["-LED-COUNT-"].update(elapsed)
    _refresh_status()


# ---------------------------------------------------------------- on_* handlers --
# all registered via @ts.bind_event; signatures mix (window, values).

# inputs tab
@ts.bind_event("-IN-NUM-")
def on_num_input(window, values):
    log(f"整数输入：{values['-IN-NUM-']!r}")


@ts.bind_event("-CB-SHOW-")
def on_show_password(window, values):
    window["-IN-PASS-"].set_password_char("" if values["-CB-SHOW-"] else "*")


@ts.bind_event("-SP-")
def on_spin(window, values):
    log(f"微调框：{values['-SP-']}")


@ts.bind_event("-SL-")
def on_slider(window, values):
    window["-PB-SL-"].update(current_value=values["-SL-"])


@ts.bind_event("-B-COLOR-")
def on_color_print(window, values):
    ml = window["-ML-"]
    ml.print("信息：原生 tk.Text 标签着色", text_color="#1565c0")
    ml.print("成功：一切正常", text_color="#2e7d32")
    ml.print("警告：一条黄色警告", text_color="#b8860b")
    ml.print("错误：一条红色错误", text_color="#c62828")


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
    log(f"查找结果：{position}")


@ts.bind_event("-B-REPLACE-")
def on_replace(window, values):
    count = ts.popup_replace(window["-ML-"])
    log(f"替换完成，共 {count} 处")


@ts.bind_event("-SUBMIT-")
def on_submit(window, values):
    log(f"表单提交：用户={values.get('-IN-USER-')!r} 数字={values.get('-IN-NUM-')!r}",
        color="#2e7d32")


# selection tab
@ts.bind_event(["-CMB-", "-OPT-", "-SP2-", "-LB-", "-CBA-", "-CBB-",
                 "-CKL-", "-R1-", "-R2-", "-R3-"])
def on_selection(window, event, values):
    log(f"选择变化：{event} = {values.get(event)!r}")


@ts.bind_event("-B-CKALL-")
def on_checklist_all(window, values):
    window["-CKL-"].check_all()
    log(f"复选列表：{window['-CKL-'].get()}")


@ts.bind_event("-B-CKNONE-")
def on_checklist_none(window, values):
    window["-CKL-"].uncheck_all()
    log(f"复选列表：{window['-CKL-'].get()}")


# data tab
@ts.bind_event("-TB-")
def on_table_select(window, values):
    table = window["-TB-"]
    records = table.selected_records
    window["-T-REC-"].update(str(records[0]) if records else "")
    log(f"表格选中：{table.get()} 记录={records[0] if records else None}")


@ts.bind_event("-B-REBIND-")
def on_rebind(window, values):
    window["-TB-"].bind([
        {"姓名": "新甲", "年龄": 21, "城市": "北京"},
        {"姓名": "新乙", "年龄": 33, "城市": "广州"},
    ])
    log("Table.bind 重新绑定完成（表头自动同步）")


@ts.bind_event("-B-ADDGRP-")
def on_tree_add_group(window, values):
    _state["tree_counter"] += 1
    key = f"grp-{_state['tree_counter']}"
    window["-TREE-"].insert_group("", key, f"分组 {_state['tree_counter']}")
    log(f"树分组：{key}")


@ts.bind_event("-B-ADD-")
def on_tree_add(window, values):
    _state["tree_counter"] += 1
    name = f"节点 {_state['tree_counter']}"
    window["-TREE-"].insert("grp-fruit", f"n{_state['tree_counter']}",
                            name, image_data=ICON16)
    log(f"树插入：{name}")


@ts.bind_event("-B-DEL-")
def on_tree_del(window, values):
    tree = window["-TREE-"]
    selection = tree.widget.selection()
    if selection:
        tree.widget.delete(*selection)
        log(f"树删除：{', '.join(str(s) for s in selection)}")
    else:
        ts.popup_notify("请先选择一个节点")


@ts.bind_event("-B-KVGET-")
def on_kv_get(window, values):
    log(f"键值编辑器：{window['-KV-'].get()}")


# graphics tab
@ts.bind_event("-GRAPH-")
def on_graph_click(window, values):
    graph = window["-GRAPH-"]
    log(f"画布点击，共 {len(graph.widget.find_all())} 个图元")


@ts.bind_event(["-CH-LINE-", "-CH-BAR-", "-CH-AREA-",
                "-CH-SCATTER-", "-CH-HBAR-", "-CH-PIE-",
                "-CH-DONUT-", "-CH-STACKED-", "-CH-HISTO-"])
def on_chart_click(window, event):
    chart = window[event]
    log(f"图表 {event} 被点击，共 {len(chart.widget.find_all())} 个图元")


@ts.bind_event("-B-CHUPD-")
def on_chart_update(window, values):
    import random

    chart = window["-CH-LINE-"]
    chart.update_data("2025", [random.randint(20, 45) for _ in range(6)])
    log("折线图 2025 系列已更新")


@ts.bind_event("-B-CHADD-")
def on_chart_add(window, values):
    import random

    chart = window["-CH-BAR-"]
    name = f"队伍 {len(chart.series_names) + 1}"
    chart.add_series(name, [random.randint(5, 30) for _ in range(4)])
    chart.redraw()
    log(f"柱状图新增系列 {name}（{chart.series_names}）")


@ts.bind_event("-B-CHPIE-")
def on_chart_pie(window, values):
    import random

    chart = window["-CH-PIE-"]
    names = ["甲", "乙", "丙", "丁"]
    pairs = [(n, random.randint(5, 60)) for n in names[: random.randint(2, 4)]]
    chart.update_data("份额", pairs)
    log(f"饼图已重掷：{pairs}")


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
    log(f"绘制 {kind} -> 图元 {figure_id}")


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
        log(f"已移动图元 {figure}")


@ts.bind_event("-B-DELF-")
def on_delete_figure(window, values):
    figure = _state["figure_last"]
    if figure is not None:
        window["-GRAPH-"].delete_figure(figure)
        log(f"已删除图元 {figure}")
        _state["figure_last"] = None


@ts.bind_event("-B-CLEARG-")
def on_clear_graph(window, values):
    window["-GRAPH-"].erase()
    _state["figure_last"] = None
    log("画布已清空")


@ts.bind_event("-CAL-")
def on_calendar(window, values):
    log(f"日历：{values['-CAL-']}")


# fancy tab (canvas-drawn widgets)
@ts.bind_event(["-RB1-", "-RB2-", "-RB3-"])
def on_round_button(window, event, values):
    log(f"圆角按钮点击：{event}")


@ts.bind_event("-IB-")
def on_image_button(window, values):
    log("图像按钮点击（整张图片都是点击区）")


@ts.bind_event("-B-TPB-ADD-")
def on_tpb_add(window, values):
    bar = window["-TPB-"]
    bar.update(current_value=min(bar.max_value, bar.get() + 10))
    log(f"文字进度条：{bar.get()}%")


@ts.bind_event("-B-TPB-ZERO-")
def on_tpb_zero(window, values):
    window["-TPB-"].update(current_value=0)
    log("文字进度条已归零")


# gauge (industrial dial)
@ts.bind_event("-SL-GAUGE-")
def on_gauge_slider(window, values):
    window["-GAUGE-"].update(values["-SL-GAUGE-"])


@ts.bind_event("-B-GAUGE-RND-")
def on_gauge_random(window, values):
    import random

    level = random.uniform(0, 100)
    temperature = random.uniform(-20, 60)
    window["-GAUGE-"].update(level)
    window["-GAUGE2-"].update(temperature)
    window["-SL-GAUGE-"].update(level)
    log(f"仪表盘：液位 {level:.1f}% / 温度 {temperature:.1f}°C")


# popup family
@ts.bind_event("-P-MSG-")
def on_p_msg(window, values):
    log(f"弹窗返回：{ts.popup('这是一个弹窗消息')!r}")


@ts.bind_event("-P-YN-")
def on_p_yn(window, values):
    log(f"popup_yes_no 返回：{ts.popup_yes_no('要继续吗？')!r}")


@ts.bind_event("-P-ERR-")
def on_p_err(window, values):
    ts.popup_error("一个错误（演示）")


@ts.bind_event("-P-SCROLL-")
def on_p_scroll(window, values):
    ts.popup_scrolled(
        "\n".join(f"第 {i} 行内容" for i in range(1, 21)),
        title="滚动文本")


@ts.bind_event("-P-TEXT-")
def on_p_text(window, values):
    log(f"popup_get_text 返回：{ts.popup_get_text('请输入点什么')!r}")


@ts.bind_event("-P-FILE-")
def on_p_file(window, values):
    log(f"选择的文件：{ts.popup_get_file('选择一个文件')!r}")


@ts.bind_event("-P-FOLDER-")
def on_p_folder(window, values):
    log(f"选择的文件夹：{ts.popup_get_folder('选择一个文件夹')!r}")


@ts.bind_event("-P-DATE-")
def on_p_date(window, values):
    log(f"选择的日期：{ts.popup_get_date()}")


@ts.bind_event("-P-FONT-")
def on_p_font(window, values):
    log(f"选择的字体：{ts.popup_get_font(include_bold_italic=True)}")


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
    log("淡出 -> 淡入（after 链式调用）")


@ts.bind_event("-W-SLIDE-")
def on_w_slide(window, values):
    start = window.current_location()
    ts.slide(window, (start[0] + 120, start[1]), duration_ms=400, steps=8,
             on_done=lambda: ts.slide(window, start, duration_ms=400, steps=8))


@ts.bind_event("-W-TOAST-")
def on_w_toast(window, values):
    window.toast("已保存", title="提示气泡", duration_ms=2500)
    log("Toast 气泡已显示（右下角淡入淡出）")


@ts.bind_event("-W-WORK-")
def on_w_work(window, values):
    ts.animate_progress(window, "-PB-WORK-", 100,
                        duration_ms=1800, steps=18,
                        on_done=lambda: window["-PB-WORK-"].update(current_value=0))
    window.perform_long_operation(
        lambda: (time.sleep(2), "后台任务完成")[1], end_key="-WORK-DONE-")
    log("后台线程已启动（界面保持响应）")


@ts.bind_event("-WORK-DONE-")
def on_work_done(window, values):
    log("perform_long_operation 返回 -WORK-DONE-", color="#2e7d32")


@ts.bind_event("-W-TIMER-")
def on_timer_on(window, values):
    _STOPWATCH["start"] = time.time()
    log("计时器已启动")


@ts.bind_event("-W-TIMEROFF-")
def on_timer_off(window, values):
    _STOPWATCH["start"] = None
    window["-T-ELAPSED-"].update("00:00")
    log("计时器已停止")


# hierarchy: a child window (parent=) with an event button inside
@ts.bind_event("-W-CHILD-")
def on_w_child(window, values):
    if _state["about_window"] is not None and not _state["about_window"].was_closed:
        _state["about_window"].bring_to_front()
        return
    child_layout = [
        [ts.TText("这是子窗口（parent=主窗口）")],
        [ts.TText("层级：child.parent == main，main.children 包含本窗口")],
        [ts.TButton("在子窗口中点击我", key="-CHILD-PING-")],
        [ts.TButton("关闭子窗口", key="-CHILD-CLOSE-")],
    ]
    _state["about_window"] = ts.Window(
        "子窗口", child_layout, finalize=True, parent=window)
    log("子窗口已打开（主窗口关闭时级联关闭）", color="#2e7d32")


@ts.bind_event("-CHILD-PING-")
def on_child_ping(window, values):
    # window is the event owner -- may be the child or the main
    log(f"子窗口按钮点击（来自 {window.title}）")


@ts.bind_event("-CHILD-CLOSE-")
def on_child_close(window, values):
    if _state["about_window"] is not None:
        _state["about_window"].close()
        _state["about_window"] = None
    log("子窗口已关闭")


# system integration
@ts.bind_event("-S-TRAY-")
def on_tray_create(window, values):
    if _TRAY["obj"] is not None:
        ts.popup_notify("托盘已存在")
        return
    try:
        _TRAY["obj"] = ts.SystemTray(title="TkSimpleGUI 演示",
                                     menu=["显示通知", "退出托盘"])
        log("托盘图标已创建（左/右键点击它）", color="#2e7d32")
    except RuntimeError as error:
        ts.popup_error(str(error))


@ts.bind_event("-S-NOTIFY-")
def on_tray_notify(window, values):
    if _TRAY["obj"] is not None:
        _TRAY["obj"].ShowMessage("TkSimpleGUI", "一条托盘气泡通知")
    else:
        ts.popup_notify("请先创建托盘")


@ts.bind_event("-S-TRAYOFF-")
def on_tray_off(window, values):
    if _TRAY["obj"] is not None:
        _TRAY["obj"].close()
        _TRAY["obj"] = None
        log("托盘已关闭")


@ts.bind_event("-S-COPY-")
def on_copy(window, values):
    window.clipboard_set(f"TkSimpleGUI 剪贴板演示 {time.time()}")
    log("已写入剪贴板")


@ts.bind_event("-S-PASTE-")
def on_paste(window, values):
    log(f"剪贴板内容：{window.clipboard_get()!r}")


@ts.bind_event("-S-SAVE-")
def on_save_state(window, values):
    _PREFS.set("last_theme", ts.theme())
    _PREFS.set("last_seen", time.strftime("%Y-%m-%d %H:%M:%S"))
    log(f"UserSettings 已保存：last_theme={_PREFS.get('last_theme')!r}, "
        f"last_seen={_PREFS.get('last_seen')}")


@ts.bind_event("-S-I18N-")
def on_i18n(window, values):
    ts.set_translations({"打开": "Ouvrir", "保存": "Sauver"})
    sample = [ts._("打开"), ts._("保存"), ts._("未注册的原样返回")]
    log(f"i18n：{' / '.join(sample)}")
    ts.clear_translations()


# menu / toolbar / right-click shared actions
@ts.bind_event("-ACT-OPEN-")
def on_open(window, values):
    path = ts.popup_get_file("打开文件（Ctrl+O）")
    log(f"动作-打开文件：{path!r}")


@ts.bind_event("-ACT-SAVE-")
def on_save(window, values):
    path = ts.popup_get_file("保存文件（Ctrl+S）", save_as=True)
    log(f"动作-保存文件：{path!r}")


@ts.bind_event("-ACT-CLEAR-")
def on_clear_log(window, values):
    window["-LOG-"].clear()
    log("日志已清空")


@ts.bind_event("-ACT-ABOUT-")
def on_about(window, values):
    ts.popup_ok(
        f"TkSimpleGUI {ts.__version__}\n\n基于 PySimpleGUI 4.x 的面向对象重写分支\n"
        "零依赖 / Python 3.7+ / 默认原生外观",
        title="关于")


@ts.bind_event("复制日志")
def on_copy_log(window, values):
    window.clipboard_set(window["-LOG-"].get())
    ts.popup_notify("日志已复制到剪贴板")


@ts.bind_event(list(_THEME_MENU_LABELS))
def on_theme(window, event, values):
    name = ts.theme(_THEME_MENU_LABELS.get(event, event))
    window.update_theme()
    log(f"主题已切换为 {name}（实时生效）", color="#1565c0")


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
    window.update_theme()
    log(f"默认主题已设为 {applied}（本窗口实时生效）", color="#2e7d32")


@ts.bind_event("-TOOL-NEW-")
def on_tool_new(window, values):
    log("工具栏：新建")


@ts.bind_event("退出")
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
