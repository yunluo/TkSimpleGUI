#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PySimpleGUI4 全功能演示。

展示库内全部元素与基础设施：ActionList、右键菜单、定时器、后台线程、
动画、剪贴板、UserSettings、i18n、SystemTray、弹窗家族、表格编辑排序、
图形句柄、滚动/分栏/流式容器等。

运行::

    python demo.py            # 交互模式
    python demo.py --smoke    # 自检：构建窗口、泵 2 秒事件、自动退出
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

_STOPWATCH = {"handle": None, "start": None}
_TRAY = {"obj": None}
_PREFS = sg.UserSettings("demo.json")


def log(window, text, color=None):
    """往底部事件日志追加一行（可着色）。"""
    window["-LOG-"].print(time.strftime("[%H:%M:%S] ") + text, text_color=color)


# ---------------------------------------------------------------- 标签页布局 --
def tab_inputs():
    band_top = sg.Column([
        [sg.Column([[sg.Text("整数校验（只许数字）")],
                    [sg.Input("", key="-IN-NUM-", size=(12, 1), validate="key",
                              validate_command=sg.validate_integer,
                              enable_events=True)]]),
         sg.Column([[sg.Text("密码")],
                    [sg.Input("", key="-IN-PASS-", size=(12, 1), password_char="*")],
                    [sg.Checkbox("显示密码", key="-CB-SHOW-", enable_events=True)]]),
         sg.Column([[sg.LabeledEdit("用户名", "yunluo", key="-IN-USER-")],
                    [sg.Submit("提交表单", key="-SUBMIT-")]]),
         sg.Column([[sg.Text("微调")],
                    [sg.Spin([str(n) for n in range(1, 11)], initial_value="5",
                             key="-SP-", enable_events=True)]])],
    ])
    band_slider = sg.Column([
        [sg.Text("滑杆联动进度条：")],
        [sg.Slider((0, 100), default_value=30, key="-SL-",
                   enable_events=True, size=(18, 15)),
         sg.ProgressBar(100, current_value=30, size=(20, 12), key="-PB-SL-")],
    ])
    band_multiline = sg.Column([
        [sg.Multiline("多行文本区域（支持撤销/重做/彩色输出/查找替换）\n",
                      key="-ML-", size=(56, 5))],
        [sg.Button("彩色输出", key="-B-COLOR-"), sg.Button("撤销", key="-B-UNDO-"),
         sg.Button("重做", key="-B-REDO-"), sg.Button("查找", key="-B-FIND-"),
         sg.Button("替换", key="-B-REPLACE-"), sg.Button("清空", key="-B-CLEAR-ML-")],
    ])
    return [[band_top], [band_slider], [band_multiline]]


def tab_selection():
    band = sg.Column([
        [sg.Column([[sg.Text("下拉")],
                    [sg.Combo(["红色", "绿色", "蓝色"], default_value="红色",
                              key="-CMB-", enable_events=True)],
                    [sg.Text("OptionMenu")],
                    [sg.OptionMenu(["甲", "乙", "丙"], key="-OPT-",
                                   enable_events=True)],
                    [sg.Text("微调")],
                    [sg.Spin(["低", "中", "高"], initial_value="中",
                             key="-SP2-", enable_events=True)]],
                   ),
         sg.Column([[sg.Text("列表（多选）")],
                    [sg.Listbox(["项目一", "项目二", "项目三", "项目四"],
                                size=(14, 4), select_mode=sg.SelectMode.EXTENDED,
                                key="-LB-", enable_events=True)]]),
         sg.Column([[sg.Text("复选")],
                    [sg.Checkbox("复选 A", key="-CBA-", enable_events=True)],
                    [sg.Checkbox("复选 B", key="-CBB-", enable_events=True)]]),
         sg.Column([[sg.Text("勾选列表")],
                    [sg.CheckList(["西瓜", "苹果", "香蕉"],
                                  default_checked=["苹果"], key="-CKL-",
                                  enable_events=True)],
                    [sg.Button("全选", key="-B-CKALL-"),
                     sg.Button("全不选", key="-B-CKNONE-")]]),
         sg.Column([[sg.Text("单选（互斥）")],
                    [sg.Radio("方案一", "plan", default=True, key="-R1-",
                              enable_events=True)],
                    [sg.Radio("方案二", "plan", key="-R2-", enable_events=True)],
                    [sg.Radio("方案三", "plan", key="-R3-", enable_events=True)],
                    [sg.CloseButton("关闭窗口", key="-CLOSE-")]]),
         ]],
    )
    return [[band]]


def tab_data():
    records = [
        {"姓名": "云落", "年龄": 30, "城市": "深圳"},
        {"姓名": "小明", "年龄": 24, "城市": "杭州"},
        {"姓名": "阿强", "年龄": 36, "城市": "成都"},
        {"姓名": "小美", "年龄": 28, "城市": "上海"},
    ]
    table = sg.Table([], headings=[], key="-TB-", enable_edit=True,
                     row_icons=[ICON16, ICON16, ICON16, ICON16], num_rows=5,
                     auto_size_columns=False, col_widths=[10, 8, 10])
    table.bind(records)
    tree = sg.Tree(headings=["节点"], show_headings=False, num_rows=6, key="-TREE-")
    kv = sg.KeyValueEditor([("主机", "localhost"), ("端口", "5432")], key="-KV-")
    band = sg.Column([
        [sg.Column([[sg.Text("表格：点表头排序 / 双击编辑 / 行图标")],
                    [table],
                    [sg.Button("换一批数据", key="-B-REBIND-"),
                     sg.Text("选中记录："),
                     sg.Text("", key="-T-REC-", size=(22, 1))]]),
         sg.Column([[sg.Text("树（带图标）")],
                    [tree],
                    [sg.Button("加节点", key="-B-ADD-"),
                     sg.Button("删节点", key="-B-DEL-")]]),
         sg.Column([[sg.Text("键值编辑器（TValEdit）")],
                    [kv],
                    [sg.Button("读取键值", key="-B-KVGET-")]])],
    ])
    return [[band]]


def tab_graphics():
    graph = sg.Graph((320, 160), (0, 0), (100, 54), key="-GRAPH-",
                     enable_events=True, background_color="#ffffff")
    return [
        [sg.Column([[sg.Text("Graph（用户坐标系 + 图元句柄）—— 点击画布有反馈")],
                    [graph],
                    [sg.Button("画圆", key="-B-CIRCLE-"),
                     sg.Button("画矩形", key="-B-RECT-"),
                     sg.Button("画字", key="-B-TEXT-"),
                     sg.Button("移动图形", key="-B-MOVEF-"),
                     sg.Button("删除最后", key="-B-DELF-"),
                     sg.Button("清空", key="-B-CLEARG-")]])],
        [sg.Column([[sg.Text("Shape / Canvas / Image")],
                    [sg.Shape("rectangle", size=(46, 22), fill_color="#3a7bd5"),
                     sg.Shape("oval", size=(46, 22), fill_color="#4caf50"),
                     sg.Shape("triangle", size=(40, 22), fill_color="#ff9800"),
                     sg.Shape("line", size=(40, 22), line_color="#666666"),
                     sg.VerticalSeparator(),
                     sg.Canvas((70, 40), background_color="#e8eef7"),
                     sg.VerticalSeparator(),
                     sg.Image(data_base64=sg.DEFAULT_BASE64_ICON)]])],
    ]


def tab_containers():
    frame = sg.Frame("分组框 Frame", [[sg.Input("框内输入", key="-IN-FRAME-")],
                                     [sg.Checkbox("框内选项", default=True)]])
    splitter = sg.Splitter(
        [[[sg.Text("左窗格")], [sg.Listbox(["A", "B", "C"], size=(9, 3))]],
         [[sg.Text("右窗格（拖动分隔条）")], [sg.Input("拖我", size=(18, 1))]]],
        key="-SPLIT-")
    scroll = sg.ScrollableColumn(
        [[sg.Text(f"  滚动行 {i:>2d} ")] for i in range(1, 21)],
        size=(140, 110), key="-SCROLL-", background_color="#f7f7f7")
    flow = sg.FlowPanel(
        [sg.Button(f"按钮 {i}", size=(6, 1)) for i in range(1, 9)],
        wrap_width=640, key="-FLOW-")
    calendar = sg.Calendar(key="-CAL-", enable_events=True)
    band_top = sg.Column([
        [sg.Column([[sg.Text("Frame")], [frame]]),
         sg.VerticalSeparator(),
         sg.Column([[sg.Text("Splitter（拖中间分隔条）")], [splitter]])],
    ])
    band_mid = sg.Column([
        [sg.Column([[sg.Text("ScrollableColumn（滚轮滚动）")], [scroll]]),
         sg.VerticalSeparator(),
         sg.Column([[sg.Text("Column（普通容器列）")],
                    [sg.Column([[sg.Text("内部元素一")],
                                [sg.Text("内部元素二")],
                                [sg.Button("列内按钮")]])]]),
         sg.VerticalSeparator(),
         sg.Column([[sg.Text("Calendar（内嵌日历）")], [calendar]])],
    ])
    band_flow = sg.Column([
        [sg.Text("FlowPanel（拖拽窗口宽度看自动换行）")],
        [flow],
    ])
    return [[band_top], [band_mid], [band_flow]]


def tab_system():
    return [
        [sg.Column([[sg.Text("弹窗家族")],
                    [sg.Button("消息", key="-P-MSG-"), sg.Button("Yes/No", key="-P-YN-"),
                     sg.Button("错误", key="-P-ERR-"), sg.Button("滚动文本", key="-P-SCROLL-"),
                     sg.Button("输入框", key="-P-TEXT-"), sg.Button("选文件", key="-P-FILE-"),
                     sg.Button("选目录", key="-P-FOLDER-"), sg.Button("选日期", key="-P-DATE-"),
                     sg.Button("选字体", key="-P-FONT-")]])],
        [sg.Column([[sg.Text("窗口控制（QWidget 运行时 API）")],
                    [sg.Button("居中", key="-W-CENTER-"), sg.Button("最大化", key="-W-MAX-"),
                     sg.Button("最小化", key="-W-MIN-"), sg.Button("还原", key="-W-NORM-"),
                     sg.Button("半透明", key="-W-ALPHA-"), sg.Button("不透明", key="-W-ALPHA1-"),
                     sg.Button("淡出淡入", key="-W-FADE-"), sg.Button("滑走再滑回", key="-W-SLIDE-")]])],
        [sg.Column([[sg.Text("后台与定时（QThread/QTimer 对标）")],
                    [sg.Button("后台任务(2秒)", key="-W-WORK-"),
                     sg.ProgressBar(100, current_value=0, size=(22, 12), key="-PB-WORK-"),
                     sg.Button("秒表开", key="-W-TIMER-"), sg.Button("秒表关", key="-W-TIMEROFF-"),
                     sg.Text("00:00", key="-T-ELAPSED-", size=(8, 1))]])],
        [sg.Column([[sg.Text("系统集成")],
                    [sg.Button("托盘：创建", key="-S-TRAY-"), sg.Button("托盘：通知", key="-S-NOTIFY-"),
                     sg.Button("托盘：关闭", key="-S-TRAYOFF-"),
                     sg.Button("写剪贴板", key="-S-COPY-"), sg.Button("读剪贴板", key="-S-PASTE-"),
                     sg.Button("保存状态", key="-S-SAVE-"), sg.Button("i18n 演示", key="-S-I18N-")],
                    [sg.Text("托盘图标出现后可左键/右键它；状态由 UserSettings 持久化。",
                             text_color="#888888")]])],
    ]


# ---------------------------------------------------------------- 行为处理 --
class Demo(object):
    def __init__(self, smoke=False):
        self.smoke = smoke
        self.figure_count = 0
        self.figure_last = None
        self.tree_counter = 0
        self.window = None
        self.actions = []

    # --- 组装 ---------------------------------------------------------------
    def build(self):
        open_action = sg.Action("打开文件", key="-ACT-OPEN-", shortcut="<Control-o>")
        save_action = sg.Action("保存文件", key="-ACT-SAVE-", shortcut="<Control-s>")
        clear_action = sg.Action("清空日志", key="-ACT-CLEAR-")
        about_action = sg.Action("关于", key="-ACT-ABOUT-")
        self.actions = [open_action, save_action, clear_action, about_action]
        menu_def = [
            ["&文件", ["打开文件", "保存文件", "---", "退出"]],
            ["&主题", ["原生外观", "DarkBlue3 主题"]],
            ["&帮助", ["关于"]],
        ]
        toolbar = sg.Toolbar([
            ("新建", "-TOOL-NEW-"), ("打开文件", "-ACT-OPEN-"),
            ("保存文件", "-ACT-SAVE-"), "---", ("关于", "-ACT-ABOUT-"),
        ])
        tabs = sg.TabGroup(
            [[sg.Tab("输入", tab_inputs()), sg.Tab("选择", tab_selection()),
              sg.Tab("数据", tab_data()), sg.Tab("绘图", tab_graphics()),
              sg.Tab("容器", tab_containers()), sg.Tab("系统", tab_system())]],
            key="-TABS-", expand_x=True, expand_y=True)
        log_element = sg.Output(size=(96, 7), key="-LOG-", expand_x=True)
        log_element.right_click_menu = ["&日志", ["复制日志", "清空日志"]]
        layout = [
            [sg.Menu(menu_def)],
            [toolbar],
            [tabs],
            [sg.Column([[sg.Text("事件日志（右键可复制/清空）")], [log_element]],
                       expand_x=True)],
            [sg.StatusBar("", key="-STATUS-", expand_x=True), sg.Sizegrip()],
        ]
        self.window = sg.Window(
            "PySimpleGUI4 功能全景演示",
            layout,
            finalize=True,
            resizable=True,
            margins=(8, 6),
            actions=self.actions,
            right_click_menu=["&窗口", ["清空日志", "关于"]],
        )
        self._post_build()
        return self.window

    def _post_build(self):
        window = self.window
        # 树节点（带图标）
        tree = window["-TREE-"]
        tree.insert("", "root", "根节点", image_data=ICON16)
        tree.insert("root", "child1", "子节点 1", image_data=ICON16)
        tree.insert("root", "child2", "子节点 2", image_data=ICON16)
        # Graph 初始图形
        graph = window["-GRAPH-"]
        graph.draw_circle((25, 40), 10, fill_color="#3a7bd5")
        graph.draw_line((0, 5), (100, 5), color="#cccccc")
        graph.draw_text("坐标 (50, 30)", (50, 30), color="#333333")
        self.figure_last = ("text", None)
        # 状态栏：启动次数（UserSettings 持久化）
        count = (_PREFS.get("launches") or 0) + 1
        _PREFS.set("launches", count)
        self._refresh_status()
        # 每秒刷新状态栏时钟（TTimer 对标）
        window.every(1000, self._tick_clock)
        log(window, f"欢迎使用 PySimpleGUI4 {sg.__version__} —— 六个标签页覆盖全部元素")
        log(window, "菜单/工具栏/右键共享 Action；Ctrl+O 打开、Ctrl+S 保存",
            color="#2e7d32")

    def _refresh_status(self):
        count = _PREFS.get("launches") or 0
        self.window["-STATUS-"].update(
            f" 就绪 | {time.strftime('%H:%M:%S')} | 第 {count} 次启动 ")

    def _tick_clock(self):
        if _STOPWATCH["start"] is not None:
            elapsed = int(time.time() - _STOPWATCH["start"])
            self.window["-T-ELAPSED-"].update(f"{elapsed // 60:02d}:{elapsed % 60:02d}")
        self._refresh_status()

    # --- 事件分发 --------------------------------------------------------------
    def dispatch(self, event, values):
        if event is None or event == sg.TIMEOUT_KEY:
            return
        handler = _DISPATCH.get(event)
        if handler is not None:
            handler(self, values)
        else:
            log(self.window, f"事件: {event!r}")

    # 输入页
    def on_num_input(self, values):
        log(self.window, f"整数校验输入: {values['-IN-NUM-']!r}")

    def on_show_password(self, values):
        element = self.window["-IN-PASS-"]
        element.set_password_char("" if values["-CB-SHOW-"] else "*")

    def on_spin(self, values):
        log(self.window, f"Spin: {values['-SP-']}")

    def on_slider(self, values):
        self.window["-PB-SL-"].update(current_value=values["-SL-"])

    def on_color_print(self, _values):
        ml = self.window["-ML-"]
        ml.print("信息：tk.Text 原生 tag 上色", text_color="#1565c0")
        ml.print("成功：一切正常", text_color="#2e7d32")
        ml.print("警告：这是黄色警告", text_color="#b8860b")
        ml.print("错误：这是红色错误", text_color="#c62828")

    def on_find(self, _values):
        position = sg.popup_find(self.window["-ML-"])
        log(self.window, f"查找结果: {position}")

    def on_replace(self, _values):
        count = sg.popup_replace(self.window["-ML-"])
        log(self.window, f"替换完成，共 {count} 处")

    def on_submit(self, values):
        log(self.window,
            f"表单提交：用户名={values.get('-IN-USER-')!r} 数字={values.get('-IN-NUM-')!r}",
            color="#2e7d32")

    # 选择页
    def on_selection(self, event, values):
        log(self.window, f"选择变化: {event} = {values.get(event)!r}")

    def on_checklist_all(self, _values):
        self.window["-CKL-"].check_all()
        log(self.window, f"勾选列表: {self.window['-CKL-'].get()}")

    def on_checklist_none(self, _values):
        self.window["-CKL-"].uncheck_all()
        log(self.window, f"勾选列表: {self.window['-CKL-'].get()}")

    # 数据页
    def on_table_select(self, values):
        table = self.window["-TB-"]
        records = table.selected_records
        self.window["-T-REC-"].update(str(records[0]) if records else "")
        log(self.window, f"表格选中: {table.get()} 记录={records[0] if records else None}")

    def on_rebind(self, _values):
        table = self.window["-TB-"]
        table.bind([
            {"姓名": "新甲", "年龄": 21, "城市": "北京"},
            {"姓名": "新乙", "年龄": 33, "城市": "广州"},
        ])
        log(self.window, "Table.bind 换数据完成（表头列自动同步）")

    def on_tree_add(self, _values):
        self.tree_counter += 1
        name = f"节点 {self.tree_counter}"
        self.window["-TREE-"].insert("root", f"n{self.tree_counter}",
                                     name, image_data=ICON16)
        log(self.window, f"树插入: {name}")

    def on_tree_del(self, _values):
        tree = self.window["-TREE-"]
        selection = tree.widget.selection()
        if selection:
            tree.widget.delete(*selection)
            log(self.window,
                f"树删除: {', '.join(str(s) for s in selection)}")
        else:
            sg.popup_notify("请先选中一个节点")

    def on_kv_get(self, _values):
        log(self.window, f"KeyValueEditor: {self.window['-KV-'].get()}")

    # 绘图页
    def on_graph_click(self, _values):
        graph = self.window["-GRAPH-"]
        log(self.window, f"画布点击，当前图元 {len(graph.widget.find_all())} 个")

    def on_draw(self, kind, _values):
        graph = self.window["-GRAPH-"]
        self.figure_count += 1
        x = 10 + (self.figure_count * 13) % 80
        if kind == "circle":
            figure_id = graph.draw_circle((x, 35), 6, fill_color="#e91e63")
        elif kind == "rect":
            figure_id = graph.draw_rectangle((x, 28), (x + 8, 42),
                                             fill_color="#4caf50")
        else:
            figure_id = graph.draw_text("字", (x, 15), color="#1565c0")
        self.figure_last = figure_id
        log(self.window, f"绘制 {kind} -> 图元 id {figure_id}")

    def on_move_figure(self, _values):
        if self.figure_last is not None:
            self.window["-GRAPH-"].move_figure(self.figure_last, 3, 2)
            log(self.window, f"移动图元 id {self.figure_last}")

    def on_delete_figure(self, _values):
        if self.figure_last is not None:
            self.window["-GRAPH-"].delete_figure(self.figure_last)
            log(self.window, f"删除图元 id {self.figure_last}")
            self.figure_last = None

    def on_clear_graph(self, _values):
        self.window["-GRAPH-"].erase()
        self.figure_last = None
        log(self.window, "画布已清空")

    def on_calendar(self, values):
        log(self.window, f"日历选择: {values['-CAL-']}")

    # 弹窗家族
    def on_p_msg(self, _values):
        log(self.window, f"popup 返回: {sg.popup('这是 popup 消息')!r}")

    def on_p_yn(self, _values):
        log(self.window, f"popup_yes_no 返回: {sg.popup_yes_no('确定继续？')!r}")

    def on_p_err(self, _values):
        sg.popup_error("出错了（演示）")

    def on_p_scroll(self, _values):
        sg.popup_scrolled(
            "\n".join(f"第 {i} 行内容" for i in range(1, 21)),
            title="滚动文本")

    def on_p_text(self, _values):
        log(self.window,
            f"popup_get_text 返回: {sg.popup_get_text('请输入一句话')!r}")

    def on_p_file(self, _values):
        log(self.window, f"选择的文件: {sg.popup_get_file('选个文件')!r}")

    def on_p_folder(self, _values):
        log(self.window, f"选择的目录: {sg.popup_get_folder('选个目录')!r}")

    def on_p_date(self, _values):
        log(self.window, f"选择的日期: {sg.popup_get_date()}")

    def on_p_font(self, _values):
        log(self.window, f"选择的字体: {sg.popup_get_font(include_bold_italic=True)}")

    # 窗口控制
    def on_w_center(self, _values):
        self.window.move_to_center()

    def on_w_max(self, _values):
        self.window.maximize()

    def on_w_min(self, _values):
        self.window.minimize()

    def on_w_norm(self, _values):
        self.window.normal()

    def on_w_alpha(self, _values):
        self.window.set_alpha_channel(0.5)

    def on_w_alpha1(self, _values):
        self.window.set_alpha_channel(1.0)

    def on_w_fade(self, _values):
        window = self.window
        sg.fade_out(window, duration_ms=400, steps=8,
                    on_done=lambda: window.after(
                        150, lambda: sg.fade_in(window, duration_ms=400, steps=8)))
        log(self.window, "淡出→淡入（after 链）")

    def on_w_slide(self, _values):
        window = self.window
        start = window.current_location()
        sg.slide(window, (start[0] + 120, start[1]), duration_ms=400, steps=8,
                 on_done=lambda: sg.slide(window, start, duration_ms=400, steps=8))

    def on_w_work(self, _values):
        sg.animate_progress(self.window, "-PB-WORK-", 100,
                            duration_ms=1800, steps=18,
                            on_done=lambda: self.window["-PB-WORK-"].update(
                                current_value=0))
        self.window.perform_long_operation(
            lambda: (time.sleep(2), "后台任务完成")[1], end_key="-WORK-DONE-")
        log(self.window, "后台线程已启动（期间界面可正常操作）")

    def on_work_done(self, _values):
        log(self.window, "perform_long_operation 返回 -WORK-DONE-", color="#2e7d32")

    def on_timer_on(self, _values):
        _STOPWATCH["start"] = time.time()
        log(self.window, "秒表已启动")

    def on_timer_off(self, _values):
        _STOPWATCH["start"] = None
        self.window["-T-ELAPSED-"].update("00:00")
        log(self.window, "秒表已停止")

    # 系统集成
    def on_tray_create(self, _values):
        if _TRAY["obj"] is not None:
            sg.popup_notify("托盘已存在")
            return
        try:
            _TRAY["obj"] = sg.SystemTray(title="PySimpleGUI4 演示",
                                         menu=["显示通知", "退出托盘"])
            log(self.window, "托盘图标已创建（左键/右键它有事件与菜单）",
                color="#2e7d32")
        except RuntimeError as error:
            sg.popup_error(str(error))

    def on_tray_notify(self, _values):
        if _TRAY["obj"] is not None:
            _TRAY["obj"].ShowMessage("PySimpleGUI4", "这是托盘气泡通知")
        else:
            sg.popup_notify("先创建托盘")

    def on_tray_off(self, _values):
        if _TRAY["obj"] is not None:
            _TRAY["obj"].close()
            _TRAY["obj"] = None
            log(self.window, "托盘已关闭")

    def on_copy(self, _values):
        self.window.clipboard_set(f"PySimpleGUI4 剪贴板演示 {time.time()}")
        log(self.window, "已写入剪贴板")

    def on_paste(self, _values):
        log(self.window, f"剪贴板内容: {self.window.clipboard_get()!r}")

    def on_save_state(self, _values):
        _PREFS.set("last_theme", sg.theme())
        _PREFS.set("last_seen", time.strftime("%Y-%m-%d %H:%M:%S"))
        log(self.window,
            f"UserSettings 已保存: last_theme={_PREFS.get('last_theme')!r}, "
            f"last_seen={_PREFS.get('last_seen')}")

    def on_i18n(self, _values):
        sg.set_translations({"Open": "打开", "Save": "保存"})
        sample = [sg._("Open"), sg._("Save"), sg._("Unknown stays")]
        log(self.window, f"i18n: {' / '.join(sample)}")
        sg.clear_translations()

    # 菜单/工具栏/右键共享
    def on_open(self, _values):
        path = sg.popup_get_file("打开（Ctrl+O）")
        log(self.window, f"Action 打开文件: {path!r}")

    def on_save(self, _values):
        path = sg.popup_get_file("保存（Ctrl+S）", save_as=True)
        log(self.window, f"Action 保存文件: {path!r}")

    def on_clear_log(self, _values):
        self.window["-LOG-"].clear()
        log(self.window, "日志已清空")

    def on_about(self, _values):
        sg.popup_ok(
            f"PySimpleGUI4 {sg.__version__}\n\nOO 重写的 PySimpleGUI 4.x 分支\n"
            "零依赖 / Python 3.7+ / 原生默认外观",
            title="关于")

    def on_copy_log(self, _values):
        self.window.clipboard_set(self.window["-LOG-"].get())
        sg.popup_notify("日志已复制到剪贴板")

    def on_theme(self, values):
        if values == "DarkBlue3 主题":
            name = sg.theme("DarkBlue3")
        else:
            name = sg.theme(None)
        log(self.window, f"主题已切换为 {name}（对新建窗口生效，重开演示可见）",
            color="#1565c0")


_DISPATCH = {
    "-IN-NUM-": Demo.on_num_input,
    "-CB-SHOW-": Demo.on_show_password,
    "-SP-": Demo.on_spin,
    "-SL-": Demo.on_slider,
    "-B-COLOR-": Demo.on_color_print,
    "-B-UNDO-": lambda demo, v: demo.window["-ML-"].undo(),
    "-B-REDO-": lambda demo, v: demo.window["-ML-"].redo(),
    "-B-CLEAR-ML-": lambda demo, v: demo.window["-ML-"].clear(),
    "-B-FIND-": Demo.on_find,
    "-B-REPLACE-": Demo.on_replace,
    "-SUBMIT-": Demo.on_submit,
    "-CMB-": Demo.on_selection,
    "-OPT-": Demo.on_selection,
    "-SP2-": Demo.on_selection,
    "-LB-": Demo.on_selection,
    "-CBA-": Demo.on_selection,
    "-CBB-": Demo.on_selection,
    "-CKL-": Demo.on_selection,
    "-R1-": Demo.on_selection,
    "-R2-": Demo.on_selection,
    "-R3-": Demo.on_selection,
    "-B-CKALL-": Demo.on_checklist_all,
    "-B-CKNONE-": Demo.on_checklist_none,
    "-TB-": Demo.on_table_select,
    "-B-REBIND-": Demo.on_rebind,
    "-B-ADD-": Demo.on_tree_add,
    "-B-DEL-": Demo.on_tree_del,
    "-B-KVGET-": Demo.on_kv_get,
    "-GRAPH-": Demo.on_graph_click,
    "-B-CIRCLE-": lambda demo, v: demo.on_draw("circle", v),
    "-B-RECT-": lambda demo, v: demo.on_draw("rect", v),
    "-B-TEXT-": lambda demo, v: demo.on_draw("text", v),
    "-B-MOVEF-": Demo.on_move_figure,
    "-B-DELF-": Demo.on_delete_figure,
    "-B-CLEARG-": Demo.on_clear_graph,
    "-CAL-": Demo.on_calendar,
    "-P-MSG-": Demo.on_p_msg,
    "-P-YN-": Demo.on_p_yn,
    "-P-ERR-": Demo.on_p_err,
    "-P-SCROLL-": Demo.on_p_scroll,
    "-P-TEXT-": Demo.on_p_text,
    "-P-FILE-": Demo.on_p_file,
    "-P-FOLDER-": Demo.on_p_folder,
    "-P-DATE-": Demo.on_p_date,
    "-P-FONT-": Demo.on_p_font,
    "-W-CENTER-": Demo.on_w_center,
    "-W-MAX-": Demo.on_w_max,
    "-W-MIN-": Demo.on_w_min,
    "-W-NORM-": Demo.on_w_norm,
    "-W-ALPHA-": Demo.on_w_alpha,
    "-W-ALPHA1-": Demo.on_w_alpha1,
    "-W-FADE-": Demo.on_w_fade,
    "-W-SLIDE-": Demo.on_w_slide,
    "-W-WORK-": Demo.on_w_work,
    "-WORK-DONE-": Demo.on_work_done,
    "-W-TIMER-": Demo.on_timer_on,
    "-W-TIMEROFF-": Demo.on_timer_off,
    "-S-TRAY-": Demo.on_tray_create,
    "-S-NOTIFY-": Demo.on_tray_notify,
    "-S-TRAYOFF-": Demo.on_tray_off,
    "-S-COPY-": Demo.on_copy,
    "-S-PASTE-": Demo.on_paste,
    "-S-SAVE-": Demo.on_save_state,
    "-S-I18N-": Demo.on_i18n,
    "-ACT-OPEN-": Demo.on_open,
    "-ACT-SAVE-": Demo.on_save,
    "-ACT-CLEAR-": Demo.on_clear_log,
    "-ACT-ABOUT-": Demo.on_about,
    "复制日志": Demo.on_copy_log,
    "原生外观": Demo.on_theme,
    "DarkBlue3 主题": Demo.on_theme,
    "-TOOL-NEW-": lambda demo, v: log(demo.window, "工具栏: 新建"),
}


def main(argv=None):
    sg.set_dpi_awareness()  # Windows 高分屏清晰渲染（进程级，一次即可）
    smoke = "--smoke" in (argv or sys.argv[1:])
    demo = Demo(smoke=smoke)
    window = demo.build()
    try:
        if smoke:
            # 自检：泵 2 秒事件 + 触发若干无弹窗行为
            deadline = time.time() + 2.0
            while time.time() < deadline:
                event, values = window.read(timeout=100)
                demo.dispatch(event, values)
            window["-B-COLOR-"].click()
            demo.dispatch("-SL-", {"-SL-": 80})
            window.close()
            print("SMOKE OK")
            return 0
        while True:
            event, values = window.read(timeout=250)
            if event in (sg.WIN_CLOSED, "退出"):
                break
            demo.dispatch(event, values)
            # 托盘事件轮询（托盘与窗口是两条事件队列）
            if _TRAY["obj"] is not None:
                tray_event, _payload = _TRAY["obj"].read(timeout=0)
                if tray_event == "显示通知":
                    _TRAY["obj"].ShowMessage("PySimpleGUI4", "来自托盘菜单")
                elif tray_event == "退出托盘":
                    _TRAY["obj"].close()
                    _TRAY["obj"] = None
                    log(window, "托盘菜单：已退出托盘")
                elif tray_event not in (None, sg.TIMEOUT_KEY):
                    log(window, f"托盘事件: {tray_event}")
    finally:
        if _TRAY["obj"] is not None:
            _TRAY["obj"].close()
        window.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
