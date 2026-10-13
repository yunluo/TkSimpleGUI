# TkSimpleGUI 路线图 / TODO

> **项目总目标（2026-10-11 定）：Tk/ttk 能实现的全覆盖，Tk/ttk 实现不了的也要实现。**
> 底线：Python 3.7、零第三方依赖（3.8+；3.7 需 `typing_extensions` 条件依赖）、Tkinter/ttk 原生实现、OO 封装。
> 完成项打勾并注明 commit；每批完成后跑 `python -m pytest tests -q`（30s 超时守护）+ `python tests/check_types.py`（ty 零诊断）+ `ruff check src tests` + `python demos/showcase.py --smoke`。

## ✅ 已完成

- [x] 全新 OO 重写（5c0f61d）：Element ABC/模板方法、ThemeManager 单例、原生默认外观
- [x] 主题重设计（840b4ff）：160 套 -> 5 套（System/Slate/Daylight/Dusk/Sage），全部低饱和、耐看、工业/个人两用
- [x] P0 能力补齐（c6e4431）：metadata / pad / expand_x / expand_y / justification / right_click_menu / disabled 构造参数；颜色字体参数全覆盖 + ttk 派生样式；Window 运行时 API（maximize/minimize/normal/restore/alpha/size/move_to_center/hide/set_icon…）；perform_long_operation；右键菜单
- [x] tk/ttk 深挖 + 默认 logo（8beed18）：Graph 图元句柄（oval/arc/polygon/image + delete/move/relocate/bring/send/get_figures_at_location）、Table 表头排序、Multiline 原生 undo/redo/彩色 print/clear、Button 图片+compound、剪贴板、set_min_size、set_dpi_awareness、Tk 字标双尺寸 iconphoto（`DEFAULT_BASE64_ICON`，默认已改为跟随解释器图标）
- [x] 第一批（70412d5）：Entry 校验、Calendar、Splitter、ScrollableColumn、窗体级右键、popup_get_font、after/every 定时器、popup_find/replace
- [x] 第二批（0cb9bd1）：CheckList、Toolbar、toggle Button、LabeledEdit、KeyValueEditor、FlowPanel、Tree/Table 行图标、Table 单元格编辑、Shape
- [x] 第三批（41d7801）：ActionList、UserSettings、Table.bind、i18n、动画、SystemTray 托盘菜单、CLI+dbg
- [x] 语法现代化（963c155/5482b18）：底线 3.7，f-string/零参 super/直连 typing 全覆盖，双守卫测试

## 🎯 新阶段 · 战线 A：Tk/ttk API 全覆盖（原生能做的全部暴露）✅ 全部完成

- [x] **Element.bind(event, callback 或 key)** — 元素级任意事件绑定（`<Double-1>`/`<Motion>`/`<FocusIn>`…），回调签名 `(element, event)` 或投递 key 进窗口队列；`unbind` 对应移除；`_bind_target` 可重写点让复合元素（Multiline）绑定到内部控件
- [x] **Multiline 补全**：`scroll_y` 滚动条、`wrap` 模式（word/char/none）、`link()` 超链接（tag_bind 可点击文字→事件）、`search_all` 高亮全部匹配 + `clear_highlights`
- [x] **Image 补全（PhotoImage 原生能力）**：`zoom/subsample` 缩放参数、GIF 逐帧读取 → **GIF 动画播放**（after 循环 + `animation_control(start/delay)`）
- [x] **ttk.Spinbox 迁移**：Spin 改用 ttk.Spinbox（原生外观），主题样式 TSpinbox
- [x] **ts.ttk_theme(name) / ts.ttk_themes()**：切换底层 ttk 主题（clam/vista/aqua…），不与 160 主题冲突
- [x] **Window wm 缺口**：`set_fullscreen`、`make_toolwindow`（Win）、`transient(parent)`（真模态从属）、`stack_above`、`set_max_size`、`bell()`
- [x] **Selection（PRIMARY 选区）**：`selection_get/selection_set` 与剪贴板并列
- [x] **字体工具**：`ts.font_families()`、`ts.font_measure(text, font)`、`ts.font_actual(font)`
- [x] **独立 Menubutton / Scrollbar 元素**（目标元素暴露 `_scroll_command` 供驱动）
- [x] **Notebook 增强**：`<<NotebookTabChanged>>` 页切换事件（投递 `(key, title)`）、`enable_traversal`（Ctrl+Tab）、`update(tab=, tab_state=)` 页禁用/隐藏、`select_tab`/`current_tab`
- [x] **Style 深水区**：`window.configure_style(style, **options)` / `window.map_style(style, **state_map)` 高级钩子

## 🎯 新阶段 · 100% 类型标注 ✅ 完成

- [x] **ty 零诊断（5865778）**：370 → 0；技法：非 Optional 类级槽注解（`_widget`/`_tk_root`/`_text`…，None 初始化行加 `# ty: ignore[invalid-assignment]`）、`Element.update(*args, **kwargs)` Liskov 基签名、tk stub Literal 参数 `cast(Literal[...], x)`、popup 布局行显式 `List[ElementRow]`；守卫：`python tests/check_types.py` 进回归基线

## 🎯 新阶段 · 战线 B：Tk/ttk 做不到的也做 ✅ 全部完成

已完成 same-spirit：表格行图标(#0 列技巧)、单元格编辑(Entry 覆盖)、FlowPanel(place 重排)、ScrollableColumn、CheckList、Calendar、toggle Button、Toolbar、托盘图标+菜单(ctypes Win32)、ActionList、数据绑定。

- [x] **Canvas 自绘按钮家族（5933b9b，新 elements/fancy.py）**：`RoundButton`（圆角/圆形，smooth 多边形 + hover 变亮 + find_overlapping 命中）、`ImageButton`（任意图片整图点击 + hover 提亮）
- [x] **带文字进度条**：`TextProgressBar`（Canvas 自绘 bar+trough+居中百分比文字，ttk 做不了文字叠加）
- [x] **Toast 浮层**：`window.toast(msg, title=, duration_ms=)` 右下角淡入淡出 Toplevel，不抢焦点自动销毁
- [x] **Table 列宽拖拽事件**：Treeview 无原生列宽事件 → ButtonRelease+identify("separator") 合成 `(key, "column_resized", col, px)` 事件 + `column_width`/`set_column_width`
- [x] **Slider 数值气泡**：`show_value=True` 拖动时 Toplevel 气泡跟随滑块显示当前值（horizontal 上方 / vertical 右侧）
- [x] **Tree 分组节点**：`insert_group`（粗体 tag）/`insert_summary`（灰色汇总行）/`collapse`/`expand`/`toggle`
- [x] **Tab 关闭按钮 ×**：`enable_close=True` 标签渲染 "×"，点击尾部 18px 命中区投递 `(key, "tab_closed", title)`，`closed_tabs` 属性
- [x] **Windows 专属加码（hotkey.py，ctypes）**：`GlobalHotkeys`（RegisterHotKey + 专用 GetMessageW 线程 → write_event_value，非 Windows no-op）、`taskbar_progress(window)`（ITaskbarList3 手写 vtable 调用：set_value/set_indeterminate/set_state/clear）

## 🎯 新阶段 · 单一事件循环 ✅ 完成（1c6febd）

- [x] **全局事件总线**：`Window._event_bus` 类级队列，`_post_event` 投递 `(window, event, values快照)`；**任何** `window.read()` / `read_all_windows()` 都能消费**任何**窗口的事件（时间序）——多窗口天然支持，无需任何额外代码
- [x] **`ts.main_loop(window, app)`**：用户**零循环**。框架泵所有窗口 root → 取总线事件 → `app.apply_event`（`@app.bind_event` + `on_*` 装饰器）→ `Action` 回调 → 全部窗口关闭自动退出
- [x] **隐藏主 root 架构**：所有窗口都是隐藏 `tk.Tk` master 的 Toplevel——关闭任一窗口（含第一个）不再连带销毁其它窗口
- [x] **WIN_CLOSED 语义**：仅用户点标题栏 X 产生（程序性 close 静默）；标题栏关闭自动出 registry；`Window.close_all()` 收尾
- [x] **修复关键哨兵歧义**：WIN_CLOSED=None 与"总线空"无法区分导致的永久等待/丢事件——统一用 `queue.Empty` 作唯一无事件信号
- [x] **跨窗口测试**：互发事件、子窗口创建、on_* 分发、main_loop 全关退出、stale 事件隔离（8 个新测试）

## 🎯 新阶段 · 根对象 .run() 启动 ✅ 完成（3b81a5b）

- [x] **`ts.Window(...).run()`** —— 拿到窗口直接启动应用（未 finalize 会自动 finalize），无需 app、无需 main_loop、无需循环
- [x] **`ts.SystemTray(...).run()`** —— 托盘即应用：无主窗口、托盘菜单项就是事件，handler 开的窗口照常参与循环；托盘移除且无窗口时结束
- [x] **`ts.default_app()`** —— 全局默认事件管理器（单例），`@ts.default_app().bind_event` 装饰器注册即被 `.run()` 拾取；也可 `run(app)` 传入显式实例
- [x] 托盘锚定循环：无窗口时也泵 tk root（after 定时器照常工作）；handler 的 window 参数注入事件属主（tray 或 window）
- [x] demo 同步 `.run()` 写法；托盘退出路径的 Win32 AV 用 `os._exit` 规避（探针/测试确定化）

## 🎯 新阶段 · 逐控件核对 Tk/ttk 原生功能覆盖 ✅ 完成

对照每个控件的 Tk/ttk 原生选项和方法清单逐项核对，**补齐的缺口**（此前未暴露的原生能力）：

- [x] **Input**：`justify` 构造参数、`set/insert/delete/get_position/set_position/select_range/clear_selection`（tk.Entry 原生 API 直通）
- [x] **Combo**：`set()`、`current(get/set index)`（ttk.Combobox 原生）
- [x] **Spin**：`range_=(lo,hi)` + `increment` + `wrap` 数值模式（原生 from/to/increment/wrap）、`set()`、`values` 属性
- [x] **Checkbox**：`toggle/select/deselect`
- [x] **Radio**：`select/deselect/group_value`（组值裸访问）
- [x] **ProgressBar**：`start_indeterminate/stop_indeterminate`（原生 marquee 模式）
- [x] **Multiline**：`insert/delete/see`（tk.Text 原生 passthrough）
- [x] **Text**：`image_data/image_filename` 图文混排（compound）、`wrap_length`
- [x] **Listbox**：`see(index)/size()`
- [x] **Table/Tree**：`see(row)`
- [x] **Frame**：`label_anchor`（ttk.Labelframe 12 方位标题）
- [x] **Image**：`photo/width/height` 属性、`zoom()/subsample()` 运行时重渲染
- [x] **Canvas**：`itemconfigure/itembbox/coords/tag_bind/create_window`（原生直通，window 可嵌元素）

**核对后确认已覆盖无需补**：Button（text/disabled/image/compound/invoke）、Checkbutton 全部选项经 style/variable、Slider（from/to/orientation/value）、Menu（tearoff/separator/disabled/shortcut）、TabGroup（tab state/traversal/事件）、Scrollbar（command 双向直通）、Window wm 全集、Graph 全部 create_* + item 操作。

## 🎯 新阶段 · IDE 亲和力专项 ✅ 完成（698500d）

针对"讨厌 Tk 一切都是字符串"：新增 `src/TkSimpleGUI/enums.py`，**13 类 str 子类枚举**替代魔术字符串（枚举的值就是 Tk 字符串，与裸字符串完全互换）：

- [x] **`ts.Anchor`**（9方位）/ **`ts.LabelAnchor`**（12方位标题）/ **`ts.Justify`** / **`ts.Relief`** / **`ts.Orientation`** / **`ts.Compound`**（图文混排）/ **`ts.State`** / **`ts.WrapMode`** / **`ts.ProgressMode`** / **`ts.Cursor`** / **`ts.Color`**（常用色名，`#rrggbb` 照常可用）
- [x] **`ts.EventType`** —— 替代 `"<Button-1>"` 式事件串：`DOUBLE_CLICK`/`RIGHT_CLICK`/`FOCUS_IN`/`RETURN`... + 工厂方法 `control("o")`/`shift("F5")`/`alt("q")`/`key(name)`
- [x] **`py.typed`**（PEP 561）+ 全量 Literal 注解 —— IDE 静默识别类型、补全、查错
- [x] 控件构造参数全部接受枚举（str 子类天然兼容），枚举/字符串互换有 6 个专项测试钉住

## 🎯 新阶段 · dataclass 配置对象 ✅ 完成（5a22725）

Python 3.7 `@dataclass` 落地——不改动控件继承体系（`__slots__`/元类链保持），新增 `src/TkSimpleGUI/config.py`：

- [x] **`ts.WindowConfig`** —— 18 个窗口选项的 typed dataclass（title/layout/size/modal/resizable/parent...），`ts.Window(layout=..., config=cfg)`；显式 kwargs 覆盖 config 值
- [x] **`ts.ElementOptions`** —— 元素共享参数包（pad/expand/tooltip/right_click_menu/metadata/disabled...），**任何控件** `config=opts` 一次带全
- [x] **元类自动展开**：`ElementBaseMeta` 包装子类 `__init__` 拦截 `config=`，40 个控件构造器**零改动**即获得能力；显式 kwargs 优先于 config
- [x] 7 个专项测试（override 优先级/类型校验/layout 进 config/共享 options 复用）

## ⛔ 明确不做（零依赖边界之外，不再反复评估）

- 文件拖放（需 tkdnd 扩展）、WebView/浏览器内核、打印对话框族、TMediaPlayer、TOleContainer、数据感知 DB 控件全家、FMX 特性（3D/GPU 特效）、QSS

## 附：回归基线

- 测试：`python -m pytest tests -q`（208 个，每测试 30s 超时守护；托盘测试以子进程隔离运行，探针在 `tests/probes/`；`python -m unittest discover tests` 同样可跑）
- 类型：`python tests/check_types.py`（ty 零诊断守卫；找不到 ty 时返回非零）
- Lint：`ruff check src tests`（配置在 pyproject `[tool.ruff]`，退出码 0 为过）
- 语法：`python tests/check_syntax.py`（用当前解释器 ast 全量解析；3.7 结论需在 3.7 下运行）
- 冒烟：`python demos/showcase.py --smoke`（3.8+ 语法扫描与现代风格守卫已内置于测试套件 TestPy37Compatibility）
- 每批提交后：compileall + 上述五项 + git commit（中文 + fix:/feat:/refactor: 前缀）
