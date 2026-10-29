# TkSimpleGUI 路线图 / TODO

> **项目总目标（2026-10-11 定）：Tk/ttk 能实现的全覆盖，Tk/ttk 实现不了的也要实现。**
> 底线：Python 3.7、零第三方依赖（3.8+；3.7 需 `typing_extensions` 条件依赖）、Tkinter/ttk 原生实现、OO 封装。
> 完成项打勾并注明 commit；每批完成后跑 `python -m pytest tests -q`（30s 超时守护）+ `python tests/check_types.py`（ty 零诊断）+ `ruff check src tests` + `python demos/showcase.py --smoke`。

## ✅ 已完成

- [x] 全新 OO 重写（5c0f61d）：Element ABC/模板方法、ThemeManager 单例、原生默认外观
- [x] 主题重设计（840b4ff）：160 套 -> 5 套（System/Slate/Daylight/Dusk/Sage），全部低饱和、耐看、工业/个人两用
- [x] P0 能力补齐（c6e4431）：metadata / pad / expand_x / expand_y / justification / right_click_menu / disabled 构造参数；颜色字体参数全覆盖 + ttk 派生样式；Window 运行时 API（maximize/minimize/normal/restore/alpha/size/move_to_center/hide/set_icon…）；start_task（原名 perform_long_operation）；右键菜单
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

## ✅ 批次 A：Element Plus 风格自绘展示控件（17 个，全部完成）

对照 Element Plus 74 个组件盘点后的"零风险"第一批：全部 Canvas 自绘或既有元素组合，
零新依赖，随主题自动换色（含 native 主题下采样平台默认色）。共享绘制层
`elements/_paint.py`（palette/blend/tint/shade/roundrect/capsule/cross/check/star/多边形裁剪/
可选 Pillow 探测/系统字体定位）在这一批次里建立，图表后端与头像/水印共用同一探测缓存。

- [x] **display.py（9）**：`Tag`（胶囊/light·dark·plain 三效果/可关闭×）、`Badge`（数字/圆点/99+ 溢出）、
      `Avatar`（文字首字母 / 图片圆形裁剪，无 Pillow 时描边退化）、`Statistic`（大数字+前后缀+涨跌箭头，
      内容超宽自动加宽画布）、`Empty`（折角文档图标+说明）、`Result`（info/success/warning/error 四态圆标）、
      `Skeleton`（呼吸动画，`animated`/`start_animation`/`stop_animation`）、`Alert`（四态内嵌条+标题+关闭，
      light/dark 两效果）、`Watermark`（平铺；有 Pillow 且定位到系统字体时按角度旋转，否则水平退化）
- [x] **panels.py（4）**：`Card`（ContainerElement，标题/副标题/右上 extra + 分隔线，嵌套布局进 body）、
      `Descriptions`（标签值网格，columns/bordered/label_suffix，`update(items=)` 重建）、
      `Steps`（横向/纵向步骤条，finish/process/error/wait 四态）、`Timeline`（str / (时间, 内容) / dict 三形态输入）
- [x] **selection.py（4）**：`Segmented`（分段控制器，滑选药丸+键盘左右键+readonly）、`Rate`（星形评分，
      悬停预览+半星裁剪+readonly）、`Pagination`（页码窗口/省略号/钳位/total 文案/show_total）、
      `Transfer`（双 Listbox+四箭头，双击移动，`move_selected`/`move_all` 可编程调用）
- [x] 导出：17 个类 + 17 个 `T` 前缀别名（`TTag`…`TTransfer`）；`elements/__init__.py` 与包根同步
- [x] showcase 新增「展示控件」页（中文 UI，17 控件全演示 + 交互按钮与日志联动；页面放进
      `ScrollableColumn` 才装得下，多亏对照时发现"多元素行与宽卡片共用 grid 列"会把窗口撑到 2165px）
- [x] 44 个专项测试（267 全绿）+ 双主题（Daylight/Slate）PrintWindow 截图目检
- [x] 目检与双解释器实机抓到并修掉的 4 个真 bug：
      **Alert 构造时不写描述文字**（只有标题）、**Statistic 前缀+数字+趋势超宽被裁**（改为按内容加宽画布）、
      **Tag 的"×"在 32 位 3.7 上点不动**（Tk 8.6.9 细线命中原点判定不可靠，改成右侧 18px 区域命中）、
      **Timeline 收到 `("10:02", {…})` 时把字典 repr 画出来**（第二个槽位是 mapping 时按字段解析）

## ✅ 日志进日志框（Output 控件，2026-10-13）

用户口径："我要的日志是显示到 output 模块控件"。不做独立日志窗口、不引入第三方
日志库——`Output`（只读 Multiline）本身就是日志框，本批次在它上面加日志层。

- [x] **`src/TkSimpleGUI/logger.py`（新）**：`Logger(element, timestamp="%H:%M:%S",
      max_lines=2000, min_level="debug", colors=None, mirror=None, drain_ms=100)`
      - 级别 `debug/info/success/warning/error/critical`，配色复用批次 A 的语义色
        （info = 控件主题字色，success/warning/error 与 Alert/Result 同一套红黄绿），
        `color=` 单行覆盖，`timestamp=` 改写或关闭
      - 环形上限：`line_count` 超限即 `delete("1.0", "N.0")` 裁头部，长跑不涨内存
      - 文件镜像：`mirror="run.log"`（纯文本、逐行 flush、logger 负责关闭）
      - **线程安全**：主线程直写；工作线程进 queue，由主线程 100ms 定时器排空
        （`start_task` 里写日志不再崩 Tk）
      - **标准库桥接**：`attach_logging("INFO", "myapp")` 挂 `logging.Handler` 并把
        目标 logger 级别一并调好（可 `detach_logging()` 还原，重复 attach 不叠加）
- [x] **控件侧**：`Multiline` 增加 `log(*args, level=...)` / `logger(**options)`（惰性
      创建、`_logger` 槽位）/ `line_count`（内容行数，尾部换行不算一行）；`Output` 继承
- [x] **一行式**：包根 `ts.log("...", key="-LOG-", level=...)`（无对象写入，找不到
      日志框返回 False）+ `ts.find_log_element(key=None, window=None)`；查找规则 =
      指定 key 或最新窗口的第一个 Output/Multiline
- [x] **`Window.elements` 公开属性**（按布局顺序列出全部元素，含无 key 的）
- [x] 顺手修掉一个既有 bug：**`Output` 被 print 一次就变可编辑**（`_end_state()` 只看
      构造参数，现在 Output 恒定以 disabled 收尾）
- [x] showcase：日志随手可用（`log()` 助手改走 `ts.log`）、新增「按级别写日志」
      「标准 logging 桥接」「模拟长任务日志」三个按钮；smoke 路径覆盖前两个
- [x] 日志面板截图目检（五级配色/对齐/桥接前缀）

## 🔧 start_task 语义对齐修复（2026-10-13）

审查发现 `Window.start_task`（原 `perform_long_operation`）把**返回值本身当成事件**投递：
绑在 `end_key` 上的处理器永远收不到（showcase 完成回调是死代码、README 示例静默失效），
返回值不可哈希时还会在派发器里报 "unhashable type"。现已对齐上游 PySimpleGUI 契约：

- [x] **事件 = `end_key`，载荷 = 返回值**：完成时 `values["-DONE-"]` 是返回值（返回 None 也
      照投，`key in values` 即"完成"）；`write_event_value(key, *value)` 支持可选载荷
      （用 `*value` 而非 `value=None`：显式 None 载荷与"无载荷"仍可区分）
- [x] **失败通道**：worker 抛异常——含 `SystemExit` 这类 BaseException（否则 UI 等不到
      事件永久卡住）——异常对象作为载荷投递（`isinstance(values[end_key], BaseException)`
      判定），同时经 `TkSimpleGUI.task` logger 报出完整 traceback（日志框桥接该 logger
      即可看见），不再只进 stderr
- [x] **线程安全**：worker 只入队——`write_event_value` 把事件交给 `Window._pending_posts`，
      主线程在下一次泵（`_pump_all_roots` → `_drain_pending_posts`）做值快照并上总线；
      hotkey 泵线程同样受益。实测快照线程从 `Thread-5` 变回 `MainThread`
- [x] 顺带：`func` 非 callable 同步 `TypeError`；线程命名 `start_task:<函数名>`；默认键
      `-THREAD DONE-` 并发语义与 `BaseException` 判定写进文档串；showcase 新增
      「后台任务（失败）」按钮 + smoke 端到端断言（事件 / 载荷 / 日志框文本）
- [x] 测试 284 → 291 → 298 → 300（日志批 +7、start_task 修复 +1、Alert close/reopen +1、
      Rate/Pagination/Steps 键盘 +3、Empty 紧凑/legacy +1、Tag 真实 click +1、
      SystemTray snake_case 与别名删除 +2；覆盖绑定 end_key 处理器触发、None 返回、
      异常载荷、不可哈希返回值、快照线程身份、载荷合并与单参兼容）

## 🧹 剥离 PySimpleGUI 兼容层（2026-10-27）

定位决策：不与 PySimpleGUI 兼容，历史残留与不良 API 全部舍弃。本次删除 32 个遗产名，
公开 `__all__` 收敛到 241 项，一个概念只保留一个名字：

- [x] **纯别名删除**：`InputText`（≡Input）、`version`/`port`、`MsgBox`（≡popup）、
      `popup_quick`/`popup_quick_message`/`popup_timed`/`popup_non_blocking`（≡popup_no_buttons
      /popup_auto_close）、`Window.element`（≡find_element）、`child_windows`（≡children）、
      `restore`（≡normal）、`SystemTray.Read`/`notify`、`ProgressBar`/`TextProgressBar` 的
      `update_bar`（≡update）、`Table.bind(records)`（按参数类型切换语义的坏 API，
      调用点改 `set_records`）、`ttk_button_class`（无调用的遗留钩子）、`theme_global`
      （空函数体死代码）
- [x] **PSG 遗产删除**：`running_trinket`/`running_replit`（PSG 网页 IDE 环境探测）、
      `Translator`/`_`/`translate`/`set_translations` 全家（零使用的 i18n）、`THIS_ROW`/
      `WRITE_ONLY_KEY`（零使用哨兵）、`WINDOW_CLOSED`/`EVENT_TIMEOUT`/`EVENT_TIMER`
      双拼哨兵、`RELIEF_*` 与裸 `FLAT`/`SOLID` 等 12 个常量（`Relief` 枚举已覆盖）、
      `DEFAULT_WINDOW_ICON`（暗示一个并不存在的默认图标）
- [x] **改名去 PSG 腔**：`list_of_look_and_feel_values`→`theme_list`、`theme_add_new`→
      `theme_add`、`LOOK_AND_FEEL_TABLE`→`THEMES`；删 `set_options`/`get_options`，
      改导出 `ts.settings` 单例（包内 6 处 `settings_mod.settings` 同步改直连导入，
      规避「包属性重绑后 `from . import settings` 拿到实例」的模块影子陷阱）
- [x] **popup 家族收敛**：`popup` 删无实现的 `button_color` 形参、`popup_no_buttons` 删被
      忽略的 `non_blocking` 形参；保留 17 个真实弹窗（`popup_get_file/folder/date/font`、
      `popup_find/replace` 等）；修正 `display._on_close_event` 的过时注释（实为真实关闭
      按钮处理器，并非"无调用者的兼容遗留"）
- [x] **保留项（非 PSG 包袱，有意为之）**：`read()`/`(event, values)` 命令式 API、
      `OptionMenu`（非只读 Combo，对应真实 Tk 控件）、`itemconfig`/`itemconfigure`
      （tkinter 本就双名）
- [x] **T 前缀扶正（同日追加，用户拍板"T 开头是我的特点，必须要"）**：61 个控件类直接
      改名 TText/TInput/TButton…，非 T 拼写整体删除（顺带删 `bind_event` 的 `on_event`
      双名）；整仓脚本重命名（词边界 + `tk.`/`ttk.`/`PIL.` 限定保护），并修复两类误伤——
      Tk 概念词（`<Button-1>` 事件串 ×30、`Tab.TFrame` 样式名、`*TCombobox*Listbox`
      option 串、注释 `Alt+Tab`、_paint 的 PIL `(Image, ImageDraw)` 元组）与点号调用
      漏网（`ts.Text` 限定形式需第二遍补齐）；`test_t_prefix_is_the_only_spelling`
      断言 63 个非 T 拼写全部 AttributeError
- [x] 测试 300 → 299：删 Translator/i18n 测试（-1）；新增 `test_removed_legacy_names`
      断言 33 个遗产名 AttributeError，tray/window 层补别名移除断言；start_task 失败
      用例改截止期限泵循环——3.7 全量套件下 worker 线程调度可被推迟 >3s（环境级现象：
      32 位 3.7 + 数百窗口 churn；单测 0.2s、类隔离 1.6s 内完成，正常使用无影响）

## 📐 全量参数类型标注（2026-10-28）

用户要求"类 方法必须支持参数类型"。AST 脚本批量标注 + 人工语义校正，**公开签名 2058 个
参数（除 self/cls）标注缺失 0**，README「100% 类型标注」成真：

- [x] **共享类型别名下沉到叶模块 constants.py**（ElementKey/Color/FontSpec/Size/PadSpec/
      Justification/MenuDefinition），base.py 改为 re-export——否则 _theming→base 的导入环
      让 def 期求值的标注炸 NameError
- [x] **不引入 `from __future__ import annotations`**：有它 ruff 的 UP045/UP006 会强推
      `X | None`/内建泛型，与 3.7 下限的 typing 泛型风格冲突；标注因此 def 期求值，
      脚本保证所有引用名已导入
- [x] **批量标注器**（%TEMP% 脚本）：词表映射统一参数（key/size/pad/tooltip…布局接口 +
      语义参数）+ 字面量默认值推导 + None 默认包 Optional + 超长签名重排多行；逐文件试点
      修完 6 类脚本 bug（`**` 星号丢失、跨行参数 stop 计算、分隔逗号吞并、元组默认值
      误判签名闭合、= = 双写等）
- [x] **语义错标校正**（ty 从 182 条清到 0 的主体）：`configure_ttk(style: "ttk.Style")`、
      `run_application(anchor: "Window | SystemTray")`、`apply_event` 聚焦查找改
      `isinstance(window, Window)` 收窄、`to_hex/_native_color/palette/measure_text`
      收 `tk.Misc`（窗口也传）、图形元助手 size 收 `float`、media 的 `label:` 实为
      tk.Label、TRate 的 `colors` 是 (filled, empty) 对、`_validate_layout` 收 Any
      （config 驱动窗口传 None）
- [x] **tk-stub 限制定向豁免**（~20 处 `# ty: ignore[...]` 带原因注释）：tkinter 选项
      机制运行时丢弃 None 值而 stub 不建模（Canvas/Label 的颜色、宽高传 None）、
      `Style.configure/map` 动态 kwargs、`Misc.configure(state=...)`、字体元组——
      均为真实合法的 tk 动态 API 用法
- [x] **过程事故与修复**：ensure_imports 脚本对无导入行文件的 `open("w")` 截断竞态把
      base/containers/data/media/window 5 个文件清零（py.typed 本就空）——全部从
      git HEAD 恢复 + 重放标注与校正；__init__/base 的多行括号导入被追加脚本写坏 ×2——
      手工修复
- [x] 验证：**ruff 0 发现 + ty 0 诊断**（含警告级 unused-ignore 清理）、299 测试
      双解释器全绿（3.12 pytest / 3.7.9 32位 unittest）、44 文件语法门双解释器通过、
      showcase --smoke OK
- [x] ruff 两份二进制均已自动升级至 0.17.2，新版启用 PLR0917（位置参数过多），与
      PLR0913 同理进 ignore——位置参数构造正是本框架的布局调用约定

## 🧹 API 设计审计：不合理 API 清除（2026-10-28）

全量公开面审计（`__all__` 去重、内建遮蔽参数、PSG 腔命名、重复概念），7 项处理，
导出 176 → 170：

- [x] **删除重复概念**：`popup_ok`（≡`popup`，两者都是 OK 按钮消息框）、
      `popup_no_buttons`（收编进 `popup_notify(duration=3)`，一个概念一个名字）、
      `popup` 的 `auto_close`/`auto_close_duration` 形参（≡`popup_auto_close`）、
      `main_loop`（PSG 腔别名，`run_application`/`.run()` 是唯一入口）、
      `timer_start`/`timer_stop`/`_ModuleTimer`（模块级隐藏全局秒表，`Timer` 类已覆盖）
- [x] **删除误导命名**：`Window.hide_row`/`unhide_row`（隐藏的是元素不是行，PSG 遗留
      词汇；`window["-KEY-"].hide()` 与 `element.hide/unhide` 已覆盖）
- [x] **内建遮蔽修复**：`TAlert` 的 `type` 参数改 `status`（对齐框架既有
      `_paint.status_color`/`_status_glyph` 词汇，属性 `_type`→`_status` 同步 slots）；
      `TSlider` 的 `range` 改 `range_`（与 TSpin 既有约定一致，不再遮蔽内建）
- [x] **PSG 腔命名**：`Window.set_alpha_channel` → `set_opacity`
- [x] **`Multiline.print` → `write`**（类方法遮蔽内建 print 的坏味道；logger 桥接、
      Output 继承同步）
- [x] **`__all__` 去重**：`SelectMode` 重复项删除
- [x] 调用点全量同步：tests（main_loop→run_application、set_opacity、write、status=、
      popup_notify）、showcase（popup、set_opacity、write、status=）；遗留名断言扩充
      至 40 个
- [x] 验证：ruff 0 / ty 0、299 测试双解释器全绿、语法门双解释器、showcase --smoke OK

- [x] **命名规范全量审计（同日）**："除类可驼峰，其余一律蛇形"——AST 扫描器核对
      全部 def/class/模块级与类级赋值：公开函数与方法 100% 蛇形、类 CamelCase、
      公共常量与枚举成员 ALL_CAPS、类型别名 CamelCase（ElementKey/FontSpec/Size/
      OptionalPoint 等类型名）、私有名 `_` 前缀——**0 违规**；顺手删除 window.py 的
      死类型别名 `WindowPoint`（定义后从未使用）；kwargs 尾下划线 `from_`/`range_`
      为规避关键字的既有约定，保留

## 📋 调研报告行动项队列（从易到难，每项开始前确认）

来源：`docs/2026-10-27-tkinter-ecosystem-survey.md` 第六节。12 条建议按实现难度
重排为队列，确认一项做一项：

- [x] **1/12 README 对比定位表**（commit 7204ee4）：「与同类库对比」表——本项目
      vs FreeSimpleGUI/CustomTkinter/ttkbootstrap 12 行对比 + 一句话定位
- [x] **2/12 类级绑定**（commit 6c60f4e）：`bind_class` 每解释器只装一次——
      Ctrl+A 全选（输入框/多行框）、Return 触发 `bind_return_key=True` 的按钮、
      禁用控件悬停 arrow 光标；TButton 新参 `bind_return_key`、Window 新方法
      `register_return_key_button`；TestClassBindings 6 例
- [ ] **3/12 布局序列化（from_spec/to_spec）**：**用户拍板跳过**——布局本身已是
      纯数据（`[[...]]` 直接可 json 化），单独序列化层的收益场景不足
- [ ] **4/12 图标字体表（内嵌 ttf 字形）**：**用户拍板跳过**——与 ⛔ 清单的
      「字体图标体系」渊源太近，ttf 内嵌又有许可与体积权衡
- [x] **5/12 双向绑定 bind_var（2026-10-28）**：新模块 `binding.py` 的 `ts.Var`
      可观察值容器 + `Window.bind_var(key, var)` / `unbind_var`——
      - 写 var 扇出到全部绑定元素（跨窗口共享同一 var，写入即广播）；
        用户改动在 `_pump_all_roots` 泵心跳回拉进 var，首个偏差元素当编辑器，
        新值复制到同 var 的其余绑定元素（同 tick 只有一个偏差源，无回环）
      - 绑定时 var 值胜出（同 tk Variable 直觉；`Var()` 默认 None 不动元素，
        首泵采纳元素现值）；同 (key, var) 重复绑定是 no-op；
        契约与 `fill()` 一致：元素 `update()` 须接受 `value=`
      - `bind_var` 要求 finalize 后的窗口（与 `element.bind()` 同先例）；
        窗口关闭/被 WM 销毁（`_mark_closed`）自动从 var 解绑，无泄漏
      - `ts.Var` 导出包根；README 新增「双向绑定（ts.Var）」章节 + 特性条目；
        TestBindVar 13 例（读写/初值方向/泵回拉/多元素扇出/跨窗口/解绑/
        关闭解绑/三类守卫异常/重复绑定 no-op）
      - 过程抓到 6c60f4e 引入的两个真 bug（新测试按字母序恰好排在
        TestClassBindings 之前而显形）：
        ①类绑定安装守卫 `_CLASS_BINDINGS_DONE` 是进程级——主 root 一旦销毁
        重建，新解释器上绑定全部静默死亡（Control-A 因 Tk 8.6 Windows 原生
        就有全选而侥幸通过，真正依赖绑定的 Return/禁用光标用例失败）；守卫
        改 per-root（`_CLASS_BINDINGS_ROOT`），加回归测试
        `test_class_bindings_survive_master_root_recreation`
        ②「最后一个窗口关闭时销毁主 root」在常规 close 路径因注册表移除
        滞后永不触发（泄漏），却会被"关闭未 finalize 窗口"误触发；实装后
        3.12 套件暴露 3 例确定性失败（StringVar/PhotoImage 绑定 default
        root，解释器更替即失效）。定稿：**主 root 为进程级单例**（隐藏窗口
        约 1MB，与既有事实行为一致），删除销毁逻辑，文档串改为
        "lives until interpreter shutdown"
      - 顺带加固 3 例 event_generate 时序敏感测试（Return 键改 deadline
        读循环、禁用光标改 deadline 刷新循环、分页器键盘新增 `_key_until`
        截止期限轮询助手）——unittest 全量负载变化让既有抖动显形，
        deadline 泵模式与 start_task 用例同款
- [x] **6/12 文件拖放 `window.drop_target(func)`（2026-10-28）**：⛔ 清单
      翻案——不走 tkdnd 扩展，新私有模块 `_dnd.py` 纯 ctypes 实现
      - 路线 = windnd 同款老式 shell API：`DragAcceptFiles` 开关 +
        WndProc 子类化收 `WM_DROPFILES`（0x233）——纯窗口消息，回调由
        Tk 消息泵在**主线程**派发（read/run_application 任意泵即触发），
        无 COM/STA 复杂度；32/64 位经 `GetWindowLongPtrW`/`GetWindowLongW`
        分支处理；`DragQueryFileW` 全长宽字符路径 → str 列表
      - API：`drop_target(func)` 接受 `func([path, ...])`；`drop_target(None)`
        撤销（恢复原 WndProc + `DragAcceptFiles(False)`）；重复注册即替换；
        关窗在 `_destroy_root` 里自动撤销；要求 finalize 后窗口；
        非 Windows 抛 `NotImplementedError`（`_dnd` 模块在任意平台可导入）
      - 回调异常不穿透 WndProc：进 `TkSimpleGUI.drop` logger（attach_logging
        可见）
      - 测试 7 例：注册/撤销/替换/未 finalize 守卫/非 callable 守卫/关窗撤销/
        **伪造真实 HDROP**（GlobalAlloc DROPFILES 结构 + 宽字符文件表）走
        `_deliver_drop_files` 全真实路径（DragQueryFileW 解析 + DragFinish
        释放）+ 回调异常不抛；测试助手补 kernel32 argtypes（64 位句柄截断
        教训）；skipUnless(win32) 守卫
      - README 新增「文件拖放（Windows）」章节 + 特性条目；测试 319 → 326
- [x] **7/12 `_paint` 颜色 tween / 主题切换动画（2026-10-28）**：
      - **原语**：`_paint.ease_out_cubic(t)`（缓动曲线）+ `_paint.tween_color(
        widget, start, end, t)`（线性混色，接受 to_hex 认识的一切——hex/
        Tk 色名/原生系统色在 widget 上采样；不可解析值跳变为 start）
      - **主题切换动画**（主要落点）：`ts.theme(name, transition_ms=250)`——
        混色做在 **ThemeManager 八个取色叶点**（BACKGROUND/TEXT/INPUT/
        TEXT_INPUT/BUTTON/PROGRESS/SCROLL/COLOR_LIST 各自 `_transitioned`
        包裹），palette/configure_ttk/kwargs 助手/元素 apply_theme 等
        下游自动拿到混色值，**零元素改动**；元组/列表值逐成员混
      - 驱动：旧主题 entry 快照 → `after` 20ms 帧循环（ease-out cubic）→
        每帧 `update_theme()` 只刷顶层窗口（递归覆盖子窗口）→ 末帧精确
        新色后清态；`apply` 语义：无活窗口/任一端原生（None/System）/
        单色覆盖场景直接跳变；过渡中再调 `theme()` 会安全终止旧循环
      - `theme()` 新参 `transition_ms=0`（默认立即，签名向后兼容）；
        README 新增「主题切换动画」章节 + 特性条目
      - 测试 7 例（326 → 333）：裸 apply 不建态/前主题 entry 快照捕获/
        取色器两端点精确混值（近 0 = 旧色、钟拨完 = 精确新色）/tick 收尾
        清态/原生端点跳变/活窗口 3 秒 deadline 泵到稳定色/tween+ease
        原语数学
      - **顺手修一颗既有套件地雷**：`test_theme_version_bumps_on_change`
        调 `ts.theme_background_color("#101010")` 原地改写 THEMES["Slate"]
        条目且从不恢复——本进程内 Slate 背景色从此变 #101010，此前无测试
        在其后断言精确色值所以潜伏（我的精确色断言把它炸出）；测试改为
        save/restore entry，全量下三处连带失败（含下游 test_lifecycle 的
        窗口泄漏级联）一并消除
- [ ] **8/12 canvas 快照回归测试**：**用户拍板跳过**——截图基线跨机器/DPI
      脆弱，维护成本高于收益
- [x] **9/12 DPI 缩放（2026-10-28）**：调研报告 #3 项三件事全部落地
      - **感知（opt-in）**：`ts.settings.dpi_aware=True`（**默认 False**，
        必须在首个窗口前设置）后，首个窗口/裸根创建时自动调
        `set_dpi_awareness()`（**系统级**，拿不到回退 legacy，进程级一次
        守卫缓存；`prefer_per_monitor=False` 新参保公开 API 兼容）；顺手修
        HRESULT 语义——`SetProcessDpiAwareness` 的 E_ACCESSDENIED（已设置）
        此前被 ctypes 静默吞掉，现显式判 S_OK/E_ACCESSDENIED 为成功。
        **关键教训：感知不能默认开启**——CI 两轮归因（conftest 关 awareness
        → worker 家族测试全过；PMv2/系统级任一级别 → start_task 家族在
        pytest-timeout 下随机饿死，失败面漂移）钉死触发器是 awareness
        本身：感知进程的 Tk 8.6 消息泵在高负载下会饿死 worker 线程调度
        （2 核 CI 是放大器）。96-DPI 机器上感知本就零收益（无虚拟化），
        改 opt-in 后默认行为与历史版本逐字节一致，CI 确定性恢复；
        真实高 DPI 用户一行开启即得清晰渲染
      - **字体线**：`apply_tk_scaling` 在每个新根设 `tk scaling` =
        Tk 原生 DPI 基准 × 用户倍率——全库字号皆点数，字体与字符定宽
        控件自动跟随；**基准只捕获一次**（`winfo_fpixels('1i')` 读回的
        就是 tk scaling 本身，直接复算会复利放大——测试序列里炸出过
        interp scaling 被推到 42.3 的指数增长）
      - **像素线（opt-in）**：`ts.settings.scaling` 倍率作用于中央钩子——
        grid padx/pady（`_grid_into`）、窗口 margins/geometry/minsize/
        set_size/set_min_size、tooltip 偏移、configure_ttk 四处内边距、
        TCanvas `_canvas_size`（图表全家 + PIL 帧一致）、display 八元素
        最终尺寸；字体派生测量（measure_text）自带倍率，只缩字面量
      - **设计取舍**：像素域不随 DPI 自动缩放（默认因子恒 1）——canvas
        内部装饰字面量未逐点改写，自动缩放会出现"画布大内部不随"的
        不一致，且十余处精确值断言会在 >100% DPI 真机集体变红；
        opt-in 下 CI/真机默认零改动，既有 333 测试零改动全绿
      - 覆盖四个裸 `tk.Tk()` 处（主根/`_font_root`/`ttk_themes`/托盘泵根），
        防止先建裸根把进程锁死在 unaware
      - 测试 17 例（333 → 350）：倍率语义与校验/scale 数学/awareness 进程
        级一次缓存与 opt-out（monkeypatch 计数）/tk scaling 双断言（基准
        保持 + 倍率跟随）/端到端（元素 padx/窗口 margins/geometry deadline
        泵/minsize/TChart/TTag 画布/TNotebook.Tab padding），全部公式断言
        （预期 = `scale_px(原值)`）任意 DPI 成立；主题 setUp/tearDown 密闭
      - README 新增「DPI 缩放（Windows）」章节 + 特性条目；`scale_px`
        （非可选）/`scale_opt`/`scale_pair`（None 直通）三分，ty 零诊断
- [x] **10/12 标配对话框三件 colorpicker/fontpicker/date（2026-10-28）**：
      盘点修订——**date 与 font 弹窗已在库中**（popup_get_date 包 TCalendar
      返回 date 对象；popup_get_font 字体列表+字号+粗斜体+实时预览），
      实际工作 = 补 1 个颜色选择器 + 审计另两个
      - **新增 `popup_get_color(message, title, default_color)`**：原生
        colorchooser 包装（**用户拍板原生路线**，与 popup_get_file 包装
        filedialog / TButton.color_chooser 同款先例，零成本稳定）；返回
        "#rrggbb" 字符串（包颜色约定 Color=str），取消 None；lazy import；
        导出 171 → 172
      - **审计 popup_get_date**：删死参数 `dateformat`——它只影响
        TCalendar.get() 的格式化，而弹窗返回 `.date` 对象从不调 get()
        （月历显示也不用它）；签名 (message, title, default_date)
      - **审计 popup_get_font**：字体列表上方加过滤输入框（几百个系统
        字体滚动难找）——模块级纯函数 `_filter_families`（大小写不敏感
        子串，空 query 全过）+ `<KeyRelease>` bind 重填 listbox（popup_
        get_text 的 Return bind 同款手法）并保持当前选择
      - showcase popup 页加「颜色」demo 按钮（-P-COLOR-，不进 smoke 列表）
      - 测试 6 例（350 → 356）TestPopupPickers：mock tkinter.colorchooser.
        askcolor（hex 直通+参数透传/cancel None/标题回退）、date 签名断言
        （dateformat 已移除）、_filter_families 纯函数、**popup_get_font
        短路 read 全链路构建**（真 Window 真元素 + mock read 验证布局/
        字体填充/bind 挂接/OK 与 Cancel 路径——比 SpyWindow 更真实的
        新测试模式）；双解释器绿
- [ ] **11/12 圆角抗锯齿**：**用户拍板跳过（排队顺序调整）**——"先做 12"；
      另 DWM 圆角偏好 API 也不做（用户口味：喜欢 Win10 方方正正，
      圆角交由系统默认）
- [x] **12/12 亮暗跟随 + DWM 美化（2026-10-28）**：
      - **新模块 `_dwm.py`**（仿 _dnd.py 纪律）：纯 ctypes DwmSetWindowAttribute
        ——深色标题栏（attr 20，Win10 1809+）+ Mica/Acrylic 背景（attr 38
        + DwmExtendFrameIntoClientArea 全边距，Win11 22H2+）；HRESULT 非 0
        或 OSError → False 全静默降级；`dwm_hwnd` 用 GetParent 拿真顶层
        HWND（hotkey 先例；c_void_p restype 直接回 int——HWND restype 实例
        int() 转换不稳是探针抓到的坑）；**圆角偏好刻意不包**（用户拍板）
      - **新模块 `_appearance.py`**：`system_prefers_dark()` winreg 读
        AppsUseLightTheme（亮 1 → False，键缺失 None）；follow 轮询 =
        主根 after 2s 自续链（ThemeManager._schedule_tick 先例），系统
        亮暗翻转 → 切 `settings.theme_light`（默认 Daylight）/
        `theme_dark`（默认 Slate），映射可改；**首拍即对齐**（探针/测试
        差异炸出的真 bug：首拍只建基线会让"follow 启动时系统已暗"永远
        不切——CTk 同款启动对齐语义）；无活窗口不挂链
      - **主题×标题栏联动（本项灵魂）**：`theme_manager.is_dark` property
        （解析 DESCRIPTION 的 "dark" 标签；原生 None）+ 模块函数
        `is_dark_theme(name)`；`Window(dark_titlebar=None)` 默认自动——
        暗主题配暗标题栏、原生外观跟系统亮暗，finalize 与 update_theme
        都重应用（主题切换即跟随）；True/False 强制；`set_dark_titlebar
        (None)` 恢复自动；`set_backdrop("mica"/"acrylic"/"mica_alt"/"none")`
        运行时方法（文档诚实说明 Tk 不透明背景下材质只在裸露处可见）
      - settings +3：theme_follow_system=False / theme_light / theme_dark；
        `WindowConfig` 同步（新参数三处同步坑）；导出 172 → 174
        （system_prefers_dark/is_dark_theme）
      - 测试 13 例（356 → 369）TestDarkLightFollow：四主题亮暗判定/
        原生与未知名 None/is_dark 随当前主题/follow 三选项校验/winreg
        mock（亮暗读值+键缺失）/poll 对齐与翻转映射/start_follow 幂等
        与无偏好拒绝/dwm_hwnd 非零/dark_titlebar 自动随主题重应用
        （spy 计数）/强制与恢复/backdrop 校验/no_titlebar 跳过 DWM
- 队列余项：11 圆角抗锯齿（已跳过）——**调研报告行动项队列收官**
## ⛔ 明确不做（零依赖边界之外，不再反复评估）

- WebView/浏览器内核、打印对话框族、TMediaPlayer、TOleContainer、数据感知 DB 控件全家、FMX 特性（3D/GPU 特效）、QSS
  （**文件拖放原列于此，2026-10-28 翻案**：不走 tkdnd 扩展，`window.drop_target` 以纯 ctypes
  `WM_DROPFILES` 老式 shell 路线实现，与 windnd 同路线）
- Element Plus 对照中的"文档流概念"组件：Affix 固钉、Anchor 锚点、Backtop 回到顶部、PageHeader 页头、
  Breadcrumb（桌面无长页面滚动模型）、Row/Col 24 栅格（Tk grid 本身就是栅格）、字体图标体系
- 待评估的后续批次（未排期）：B 批弹层族（Popover/Popconfirm/Loading/Drawer/折叠面板/弹出式日期时间）、
  C 批（AutoComplete/Cascader/TreeSelect/InputTag/Upload 桌面转译）、Canvas 虚拟列表（唯一需要重写渲染层的项目）

## 附：回归基线

- 测试：`python -m pytest tests -q`（369 个，每测试 30s 超时守护；托盘测试以子进程隔离运行，探针在 `tests/probes/`；`python -m unittest discover tests` 同样可跑）
- 类型：`python tests/check_types.py`（ty 守卫；找不到 ty 时返回非零。注意 PATH 上的 ty 0.0.53 会对既有
  `elements/buttons.py` 报 34 条 ttk stub 误报——基线如此，与本批次无关；`D:\bin\ty.exe`（0.0.32）零诊断）
- Lint：`ruff check src tests demos`（配置在 pyproject `[tool.ruff]`，退出码 0 为过）
- 语法：`python tests/check_syntax.py`（用当前解释器 ast 全量解析；3.7 结论需在 3.7 下运行）
- 冒烟：`python demos/showcase.py --smoke`（3.8+ 语法扫描与现代风格守卫已内置于测试套件 TestPy37Compatibility）
- 每批提交后：compileall + 上述五项 + git commit（中文 + fix:/feat:/refactor: 前缀）
