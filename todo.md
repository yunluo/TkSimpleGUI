# PySimpleGUI4 路线图 / TODO

> **项目总目标（2026-10-11 定）：Tk/ttk 能实现的全覆盖，Tk/ttk 实现不了的也要实现。**
> 底线：Python 3.7、零第三方依赖、Tkinter/ttk 原生实现、OO 封装。
> 完成项打勾并注明 commit；每批完成后跑 `python -m unittest tests.test_package` + `python _split/oo_smoke.py`。

## ✅ 已完成

- [x] 全新 OO 重写（5c0f61d）：Element ABC/模板方法、ThemeManager 单例、原生默认外观、160 主题
- [x] P0 能力补齐（c6e4431）：metadata / pad / expand_x / expand_y / justification / right_click_menu / disabled 构造参数；颜色字体参数全覆盖 + ttk 派生样式；Window 运行时 API（maximize/minimize/normal/restore/alpha/size/move_to_center/hide/set_icon…）；perform_long_operation；右键菜单
- [x] tk/ttk 深挖 + 默认 logo（8beed18）：Graph 图元句柄（oval/arc/polygon/image + delete/move/relocate/bring/send/get_figures_at_location）、Table 表头排序、Multiline 原生 undo/redo/彩色 print/clear、Button 图片+compound、剪贴板、set_min_size、set_dpi_awareness、P4 字标双尺寸 iconphoto（生成器 `_split/gen_logo.py`）
- [x] 第一批（70412d5）：Entry 校验、Calendar、Splitter、ScrollableColumn、窗体级右键、popup_get_font、after/every 定时器、popup_find/replace
- [x] 第二批（0cb9bd1）：CheckList、Toolbar、toggle Button、LabeledEdit、KeyValueEditor、FlowPanel、Tree/Table 行图标、Table 单元格编辑、Shape
- [x] 第三批（41d7801）：ActionList、UserSettings、Table.bind、i18n、动画、SystemTray 托盘菜单、CLI+dbg
- [x] 语法现代化（963c155/5482b18）：底线 3.7，f-string/零参 super/直连 typing 全覆盖，双守卫测试

## 🎯 新阶段 · 战线 A：Tk/ttk API 全覆盖（原生能做的全部暴露）✅ 全部完成

- [x] **Element.bind(event, callback 或 key)** — 元素级任意事件绑定（`<Double-1>`/`<Motion>`/`<FocusIn>`…），回调签名 `(element, event)` 或投递 key 进窗口队列；`unbind` 对应移除；`_bind_target` 可重写点让复合元素（Multiline）绑定到内部控件
- [x] **Multiline 补全**：`scroll_y` 滚动条、`wrap` 模式（word/char/none）、`link()` 超链接（tag_bind 可点击文字→事件）、`search_all` 高亮全部匹配 + `clear_highlights`
- [x] **Image 补全（PhotoImage 原生能力）**：`zoom/subsample` 缩放参数、GIF 逐帧读取 → **GIF 动画播放**（after 循环 + `animation_control(start/delay)`）
- [x] **ttk.Spinbox 迁移**：Spin 改用 ttk.Spinbox（原生外观），主题样式 TSpinbox
- [x] **sg.ttk_theme(name) / sg.ttk_themes()**：切换底层 ttk 主题（clam/vista/aqua…），不与 160 主题冲突
- [x] **Window wm 缺口**：`set_fullscreen`、`make_toolwindow`（Win）、`transient(parent)`（真模态从属）、`stack_above`、`set_max_size`、`bell()`
- [x] **Selection（PRIMARY 选区）**：`selection_get/selection_set` 与剪贴板并列
- [x] **字体工具**：`sg.font_families()`、`sg.font_measure(text, font)`、`sg.font_actual(font)`
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

## ⛔ 明确不做（零依赖边界之外，不再反复评估）

- 文件拖放（需 tkdnd 扩展）、WebView/浏览器内核、打印对话框族、TMediaPlayer、TOleContainer、数据感知 DB 控件全家、FMX 特性（3D/GPU 特效）、QSS

## 附：回归基线

- 测试：`python -m unittest tests.test_package`（117 个，含全部批次回归；托盘测试以子进程隔离运行）
- 类型：`python tests/check_types.py`（ty 零诊断守卫）
- 冒烟：`python _split/oo_smoke.py`（32+ 项，含 3.8+ 语法扫描与现代风格守卫）+ `python demo.py --smoke`
- 每批提交后：compileall + 上述四项 + git commit（中文 + fix:/feat:/refactor: 前缀）
