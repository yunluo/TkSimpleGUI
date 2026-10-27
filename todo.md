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
- [x] ruff 两份二进制均已自动升级至 0.17.2，新版启用 PLR0917（位置参数过多），与
      PLR0913 同理进 ignore——位置参数构造正是本框架的布局调用约定

## ⛔ 明确不做（零依赖边界之外，不再反复评估）

- 文件拖放（需 tkdnd 扩展）、WebView/浏览器内核、打印对话框族、TMediaPlayer、TOleContainer、数据感知 DB 控件全家、FMX 特性（3D/GPU 特效）、QSS
- Element Plus 对照中的"文档流概念"组件：Affix 固钉、Anchor 锚点、Backtop 回到顶部、PageHeader 页头、
  Breadcrumb（桌面无长页面滚动模型）、Row/Col 24 栅格（Tk grid 本身就是栅格）、字体图标体系
- 待评估的后续批次（未排期）：B 批弹层族（Popover/Popconfirm/Loading/Drawer/折叠面板/弹出式日期时间）、
  C 批（AutoComplete/Cascader/TreeSelect/InputTag/Upload 桌面转译）、Canvas 虚拟列表（唯一需要重写渲染层的项目）

## 附：回归基线

- 测试：`python -m pytest tests -q`（298 个，每测试 30s 超时守护；托盘测试以子进程隔离运行，探针在 `tests/probes/`；`python -m unittest discover tests` 同样可跑）
- 类型：`python tests/check_types.py`（ty 守卫；找不到 ty 时返回非零。注意 PATH 上的 ty 0.0.53 会对既有
  `elements/buttons.py` 报 34 条 ttk stub 误报——基线如此，与本批次无关；`D:\bin\ty.exe`（0.0.32）零诊断）
- Lint：`ruff check src tests demos`（配置在 pyproject `[tool.ruff]`，退出码 0 为过）
- 语法：`python tests/check_syntax.py`（用当前解释器 ast 全量解析；3.7 结论需在 3.7 下运行）
- 冒烟：`python demos/showcase.py --smoke`（3.8+ 语法扫描与现代风格守卫已内置于测试套件 TestPy37Compatibility）
- 每批提交后：compileall + 上述五项 + git commit（中文 + fix:/feat:/refactor: 前缀）
