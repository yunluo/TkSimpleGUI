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

## 🎯 新阶段 · 战线 A：Tk/ttk API 全覆盖（原生能做的全部暴露）

- [ ] **Element.bind(event, callback 或 key)** — 元素级任意事件绑定（`<Double-1>`/`<Motion>`/`<FocusIn>`…），对标 Qt eventFilter 入口；回调签名 `(element, event)`
- [ ] **Multiline 补全**：`scroll_y` 滚动条（目前没有！）、`wrap` 模式（word/char/none）、`tag_bind` 超链接（可点击文字→事件）、`search_all` 高亮全部匹配
- [ ] **Image 补全（PhotoImage 原生能力）**：`zoom/subsample` 缩放参数、GIF 逐帧读取 → **GIF 动画播放**（after 循环）
- [ ] **ttk.Spinbox 迁移**：Spin 改用 ttk.Spinbox（原生外观），保留 tk 兜底参数
- [ ] **sg.ttk_theme(name)**：切换底层 ttk 主题（clam/vista/aqua…），不与 160 主题冲突
- [ ] **Window wm 缺口**：`fullscreen`、`toolwindow`（Win 无常驻按钮小窗）、`transient(parent)`（真正的模态从属窗）、`set_max_size`、`bell()`、`stack_above(other)`
- [ ] **Selection（PRIMARY 选区）**：`selection_get/selection_set` 与剪贴板并列
- [ ] **字体工具**：`sg.font_families()`、`sg.font_measure(text, font)`、`sg.font_description(font)`
- [ ] **独立 Menubutton / Scrollbar 元素**（Toolbar 内部已用，未导出）
- [ ] **Notebook 增强**：`<<NotebookTabChanged>>` 事件、`enable_traversal`（Ctrl+Tab）、`tab(state=disabled/hidden)`、Tab 关闭按钮（× 图标变体，战线 B 技法）
- [ ] **Style 深水区**：`ThemeManager.configure_ttk` 暴露 `style.map`/`layout` 自定义入口（高级用户钩子）

## 🎯 新阶段 · 战线 B：Tk/ttk 做不到的也做（组合控件 / Canvas 自绘 / ctypes）

已完成 same-spirit：表格行图标(#0 列技巧)、单元格编辑(Entry 覆盖)、FlowPanel(place 重排)、ScrollableColumn、CheckList、Calendar、toggle Button、Toolbar、托盘图标+菜单(ctypes Win32)、ActionList、数据绑定。

- [ ] **Canvas 自绘按钮家族**：`RoundButton`（圆角/圆形按钮，tag_bind 命中）、`ImageButton`（任意底图按钮）——tk 无原生圆角
- [ ] **Table 列宽拖拽**：表头分隔线命中检测 + 拖动改列宽（Treeview 无原生列拖拽）
- [ ] **Tab 关闭按钮**：Notebook 标签页带 × 关闭（tab image + 点击区域命中）
- [ ] **Toast 浮层**：窗口内右下角淡入淡出通知（Toplevel + alpha 动画 + after）
- [ ] **带文字进度条**：Canvas 自绘进度 + 百分比文字覆盖（ttk 做不了文字叠加）
- [ ] **Slider 数值气泡**：拖动时在滑块上方显示当前值
- [ ] **Windows 专属加码（ctypes）**：任务栏进度条状态（ITaskbarList3）、全局热键（RegisterHotKey）
- [ ] **多列分组 Tree**：可折叠分组节 + 汇总行样式（Treeview item tag 配色）

## ⛔ 明确不做（零依赖边界之外，不再反复评估）

- 文件拖放（需 tkdnd 扩展）、WebView/浏览器内核、打印对话框族、TMediaPlayer、TOleContainer、数据感知 DB 控件全家、FMX 特性（3D/GPU 特效）、QSS

## 附：回归基线

- 测试：`python -m unittest tests.test_package`（91 个，含三批全部回归；托盘测试以子进程隔离运行）
- 冒烟：`python _split/oo_smoke.py`（32+ 项，含 3.8+ 语法扫描与现代风格守卫）
- 每批提交后：compileall + 上述两项 + `python demo.py --smoke` + git commit（中文 + fix:/feat:/refactor: 前缀）
