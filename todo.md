# PySimpleGUI4 路线图 / TODO

> 对标基准：Qt（架构与 API 完整性）、Delphi VCL（控件面板覆盖度）。
> 底线不变：Python 3.4、零第三方依赖、Tkinter/ttk 原生实现、OO 封装。
> 完成项打勾并注明 commit；每批完成后跑 `python -m unittest tests.test_package` + `python _split/oo_smoke.py`。

## ✅ 已完成

- [x] 全新 OO 重写（5c0f61d）：Element ABC/模板方法、ThemeManager 单例、原生默认外观、160 主题
- [x] P0 能力补齐（c6e4431）：metadata / pad / expand_x / expand_y / justification / right_click_menu / disabled 构造参数；颜色字体参数全覆盖 + ttk 派生样式；Window 运行时 API（maximize/minimize/normal/restore/alpha/size/move_to_center/hide/set_icon…）；perform_long_operation；右键菜单
- [x] tk/ttk 深挖 + 默认 logo（8beed18）：Graph 图元句柄（oval/arc/polygon/image + delete/move/relocate/bring/send/get_figures_at_location）、Table 表头排序、Multiline 原生 undo/redo/彩色 print/clear、Button 图片+compound、剪贴板、set_min_size、set_dpi_awareness、P4 字标双尺寸 iconphoto（生成器 `_split/gen_logo.py`）

## 🥇 第一批：高性价比、纯 Tk 原生（Delphi Tier 1）✅ 全部完成

- [x] **Entry 输入校验**（对标 TMaskEdit）— `Input(validate="key", validate_command=...)` 暴露 tk.Entry 原生校验，内置 `validate_integer`/`validate_float`/`validate_regex`（fullmatch 语义）
- [x] **Calendar 元素**（对标 TMonthCalendar/TDateTimePicker）— `elements/calendar.py`，月视图+翻页+选中高亮+事件，`get()` 按 `dateformat` 返回；popup_get_date 已改为基于它
- [x] **Splitter 元素**（对标 TSplitter）— `tk.PanedWindow` 多窗格容器，`layouts=[...]`、`orientation`、`handle_size`（sashwidth）
- [x] **ScrollableColumn**（对标 TScrollBox）— Canvas+scrollregion+滚轮（Windows/Linux 双协议）+ 可选纵横滚动条
- [x] **窗体级右键菜单** — `Window(right_click_menu=...)`，与元素级共用 `build_popup_menu`
- [x] **popup_get_font**（对标 TFontDialog）— 字体列表+字号 Spin+Bold/Italic+实时预览
- [x] **Timer helper**（对标 TTimer）— `window.after(ms, cb)` 单次 / `window.every(ms, cb)` 循环，返回可 cancel 的 `_TimerHandle`
- [x] **popup_find / popup_replace**（对标 TFindDialog/TReplaceDialog）— 基于 tk.Text search；`_text_find`/`_text_replace_all` 可独立调用

## 🥈 第二批：控件补全（Delphi Tier 1 尾 + Tier 2）✅ 全部完成

- [x] **CheckList 元素**（对标 TCheckListBox）— 勾选列表，`default_checked`、`update(values=/checked=)`、`check_all()/uncheck_all()`，`get()` 返回选中列表
- [x] **Toolbar 元素**（对标 TToolBar）— `Toolbar(["Open", "---", ("Save", "-KEY-"), ("Options", "-KEY-", [菜单项])])`，统一按钮排 + 分隔符 + 下拉按钮（Menubutton）
- [x] **Button toggle**（对标 TSpeedButton）— `toggle=True` 按下保持（tk.Button 凹陷态）+ `group_id` 组内互斥（Window 注册表），`get()` 返回按下状态
- [x] **LabeledEdit**（对标 TLabeledEdit）— 标签+输入一体，`label_position="above"/"left"`，key 归 Input，`.input`/`.label` 属性
- [x] **KeyValueEditor**（对标 TValEdit）— `KeyValueEditor([("host","localhost"), ...])`，`get()` 返回 `{label: value}` 字典进 values
- [x] **FlowPanel**（对标 TFlowPanel）— place 重排自动换行，`horizontal_padding/vertical_padding`，resize 自适应
- [x] **Tree/Table 行图标**（对标 TImageList 轻量版）— `Tree.insert(..., image_data=/image_filename=)`；`Table(row_icons=[...])`（bytes=base64, str=文件名）
- [x] **Table 单元格编辑**（对标 TStringGrid）— `enable_edit=True` 双击编辑，提交后 `values` 同步并投递 `(key, row, col, new_value)` 元组事件
- [x] **Shape 元素**（对标 TShape/TBevel）— `Shape("rectangle"/"oval"/"triangle"/"line")`，颜色可 update

## 🥉 第三批：架构件与基础设施 ✅ 全部完成

- [x] **ActionList**（对标 TActionList / Qt QAction）— `Action(text, key, shortcut, callback)`；Window 构造参数 `actions=`：菜单/右键文本自动归一化为 key、快捷键自动绑定、事件读取时自动触发 `callback(window, values)`；`Action.to_button()` / `ActionList.menu_definition(title)`
- [x] **UserSettings**（对标 QSettings/TIniFile）— JSON 持久化（默认 `~/.pysimplegui4/`），`set/get/delete/keys`、`/` 嵌套路径、字典式访问、写入即落盘
- [x] **Table.bind(records)**（TDataSource 轻量版）— list-of-dicts 自动推列（或显式 headings），`selected_records` 取原始记录，单元格编辑回写 dict，排序同步重排记录
- [x] **i18n**（Qt tr() 简化版）— `_("Open")` + `set_translations(字典或JSON文件)` / `add_translation` / `clear_translations`，未命中原样返回
- [x] **动画 helper**（QPropertyAnimation 简化版）— `fade_in/fade_out/slide/animate_progress`，全部基于 `window.every` 返回可取消句柄
- [x] **SystemTray 托盘菜单** — 真托盘图标（ctypes 隐藏消息窗口 + WNDPROC + PNG→ICO 内存包装）+ 右键菜单（TrackPopupMenu/TPM_RETURNCMD）+ 左键/双击/气泡点击事件队列 + `read(timeout)`（复用 Tk 消息泵，独立托盘自建隐藏 root）
- [x] **CLI + dbg** — `python -m PySimpleGUI4 [--version|--themes]`（pyproject 注册 `PySimpleGUI4` 命令）；`sg.dbg(*args)` 快速调试弹窗

## ⛔ 明确不做（超出零依赖 Tkinter 边界，不再反复评估）

- 打印对话框族（TPrintDialog 等）、TMediaPlayer、TOleContainer、TAnimate
- 数据感知控件全家（TDBGrid/TDBEdit…，用上面的轻量 bind 替代）
- FMX 特性（TMultiView 抽屉、3D、GPU 特效）、tkdnd 拖放扩展
- QSS 样式表、完整 Model/View MVC（保留 values-based 声明式卖点）

## 附：回归基线

- 测试：`python -m unittest tests.test_package`（90 个，含三批全部回归；托盘测试以子进程隔离运行）
- 冒烟：`python _split/oo_smoke.py`（32 项）
- 兼容扫描：ast 检查无 f-string（test_no_fstrings）、`__slots__` 无 `__dict__`
- 每批提交后：compileall + 上述两项 + git commit（中文 + fix:/feat:/refactor: 前缀）
