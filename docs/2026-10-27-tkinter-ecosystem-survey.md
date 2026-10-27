# Python Tk/Tkinter 封装库生态调研报告

> 调研日期：2026-10-27 ｜ 调研方式：临时 venv 实装 + 源码精读 + GitHub topic 收敛 + PyPI 元数据
> 调研目的：为 TkSimpleGUI（本项目）寻找可借鉴的实现手法、使用逻辑、布局方案与差异化定位
> 结论先行：**框架层共 9 家，名单已穷尽；生态单件 30+ 家；四轮合计实装 34 个包。**
> 带走三件最重要的事：① PySimpleGUI 6 重新开源（LGPL3）；② 文件拖放可以零依赖翻案（windnd 已验证）；
> ③ 框架层的差异化机会窗口依然开着（竞品要么抬门槛要么停滞）。

---

## 一、调研方法

- **环境**：`%TEMP%\tksg_survey_venv`（Python 3.12.12 独立虚拟环境，不污染项目），累计 `pip install` 34 个包。
- **四轮推进**：
  1. 主流框架 8 家（全网搜索收敛）；
  2. 生态第二圈 12 家（PSG 分叉、主题、单件控件、窗口美化）；
  3. 第三圈 8 家 + builder 搜索（中国生态、asyncio、通知类）；
  4. 理念圈 6 家 + `topic:tkinter`（18,931 仓库）/`topic:ttk` 榜单收敛，确认无遗漏。
- **深度**：框架与理念型库精读源码（绘制引擎、事件模型、布局组织、属性系统）；
  单件控件以元数据 + 结构 + 关键文件为准；构建器类应用以仓库文档为准。
- 数字（stars/版本/日期）均为截至 2026-10-27 抓取。

---

## 二、生态全景地图

### 框架层（9 家）

| 库 | 版本 | stars | 许可证 | Python | 依赖 | 状态 |
|---|---|---|---|---|---|---|
| PySimpleGUI | 6.3.0.1 | 13,826 | **LGPL3（重新开源）** | ≥3.6 | 无 | 商业化失败后回归开源 |
| CustomTkinter | 6.0.0 | 13,591 | CC0 | ≥3.7 | darkdetect、packaging | 最热门，维护放缓 |
| ttkbootstrap | 2.2.6 | 2,662 | 未标注 | **≥3.10** | **Pillow 硬依赖** | 活跃，2.x 大改 |
| pygubu | 0.42.1 | 2,170 | — | ≥3.9 | 无（插件可选） | 稳定 |
| guizero | 1.6.0 | — | BSD | ≥3 | 无 | 缓慢（教学向） |
| FreeSimpleGUI | 5.3.0 | — | LGPL3 | 未声明 | **无** | PSG4 分叉续命，活跃 |
| TKinterModernThemes | 1.10.5 | — | MIT | ≥3.10 | 无 | 小众 |
| maliang | 3.2.0 | 1,102 | MIT | **≥3.11** | 无（扩展可选） | 活跃，中文项目 |
| tukaan | 0.2.1 | 167 | MIT | ≥3.7 | pillow + 每平台原生二进制 | **停滞**（理念标本） |
| appjar | 0.94.0 | — | Apache 2.0 | 未声明 | 无 | **已死多年**（反面教材） |

（另有 TkZero 0.2.0 停在 0.2，依赖 Pillow，纯 OO 小库，同为"API 好但无生态"标本。）

### 主题层（3 + 2 个纯 tcl 分发）

| 库 | 版本 | 许可证 | 依赖 | 说明 |
|---|---|---|---|---|
| sv-ttk | 2.6.1 | MIT | 无 | Win11 Sun Valley 风，`set_theme/toggle_theme` 三函数极简 API |
| ttkthemes | 3.3.0 | — | pillow | 老式位图主题合集（历史价值） |
| rdbende 主题群 | — | MIT | 无 | Sun Valley(2,589★)/Azure(852★)/Forest(465★)，纯 tcl 分发 |

### 单件控件层（生态"拼积木"，非框架）

| 库 | 版本 | 许可证 | 依赖 | 说明 |
|---|---|---|---|---|
| tksheet | 7.6.0 | 元数据未标 | **无** | 数据表格之王，`Sheet(tk.Frame)` 6700+ 行，7.x 重写 |
| tkcalendar | 1.6.1 | GPLv3 | babel | 日期选择器 |
| tkinterweb | 4.25.5 | MIT | tkhtml3 二进制 | HTML 渲染控件 |
| tkinterdnd2 | 0.7.0 | — | 无（带 tkdnd 二进制） | 拖放（原生扩展路线） |
| **windnd** | 1.0.7 | MIT | **无** | **拖放（纯 ctypes DragAcceptFiles + WM_DROPFILES）** |
| tkintervideo | 0.0.2 | — | 无 | 视频控件（停在 0.0.2，多媒体无成熟方案） |
| tkinter-tooltip | 3.1.2 | MIT | 近零 | 单件 tooltip，decorator 风格 API |
| ttkwidgets | 0.13.0 | **AGPL** | pillow | 杂项控件（许可传染风险） |
| tkintermapview | 1.30 | CC0 | geopy/requests/pywin32+CTk | 地图控件（依赖膨胀反面教材） |
| tkfontawesome | 0.3.2 | MIT | lxml + tksvg | 字体图标（ttkbootstrap 作者出品） |
| ttkbootstrap-icons | 5.0.0 | — | tkinter-icons | 图标集（≥3.10） |
| ctkmessagebox | 2.7 | CC0 | CTk + pillow | CTk 生态最热弹窗补件 |
| ctkmenubar | 0.9 | CC0 | customtkinter | CTk 菜单栏补件 |
| AwesomeTkinter | — | — | — | 好看控件合集（canvas/图片合成） |

### 构建器层（5 家 + 中文 IDE）

| 工具 | 形态 | 说明 |
|---|---|---|
| pygubu-designer | 桌面应用 | XML (.ui) 设计器，1,070★ |
| PAGE | Tcl 应用 | 老牌拖拽生成器，**生成 PSG 兼容代码**（PSG 契约=事实标准的旁证） |
| Tkinter-Designer | 桌面应用 | Figma→tkinter 代码，10,251★（生成 place 绝对坐标，实用性存疑） |
| PyUIBuilder | 桌面应用 | 跨 tkinter/CTk/Kivy/PySide，2,630★，2025 活跃 |
| DragDropTK | 本地工具 | 拖放式 GUI 设计工具 |
| Formation Studio | 桌面应用 | 398★，XML/JSON 设计文件 + **formation-dbg 运行时检查器**（独一份） |
| PythonIDE-PyMe | 中文 IDE | 930★，可视化开发 + 一键跨平台发布 |

### Win32 增强 / 通知层

| 库 | 版本 | 许可证 | 依赖 | 说明 |
|---|---|---|---|---|
| pywinstyles | 1.8 | CC0 | 无 | mica/acrylic/模糊/圆角/标题栏色，裸 ctypes DWM API |
| winotify | 1.1.0 | MIT | 无 | Windows toast，纯 ctypes 拼 XML |
| windows-toasts | 1.3.1 | — | WinRT 全家桶 | 同上场景的 WinRT 路线（依赖重） |
| async-tkinter-loop | 0.10.4 | MIT | 无 | Tk mainloop ↔ asyncio 桥（≥3.10） |

### 理念型 / MVVM 流派（GitHub-only 居多，PyPI 边缘）

| 库 | 理念 | 状态 |
|---|---|---|
| tkpf | tkinter 双向数据绑定 + 组件化 | 仅 GitHub |
| tkmvvm | MVVM + XML 生成界面 | 仅 GitHub |
| LayoutX | Pug 模板 + ReactiveX + Redux 式 Store | PyPI 1.2，无 license 声明 |
| Formation | 设计文件 + 运行时构建 + 热检视器 | PyPI formation-studio，MIT |

---

## 三、框架层逐家分析

### 3.1 PySimpleGUI 6 —— 契约源头，重新开源

- **重大事件**：5.x 商业化基本失败（作者自述"公司用户多、付费 license 少"），6.x 删除授权组件后以 **LGPL3 重新开源**。PyPI METADATA 原话："I've released the PySimpleGUI 5 code as open source. After removing licensing and security components, it's now available under the LGPL3 license."
- **代码形态**：仍是 24k+ 行单文件巨石（`class Element` 994 行起，`class Window` 10,201 行起，含 Debugger/UserSettings/SystemTray/popup 全家桶）。零依赖、≥3.6。
- **使用逻辑**：`layout = [[sg.Text(..), sg.Input(..)], [sg.Button(..)]]` → `window = sg.Window(..)` → `event, values = window.read()` 轮询 → `element.update(..)`。
- **对本项目的意义**：LGPL3 允许向上再许可为 GPL3（本项目 GPL-3.0-or-later），参照其契约学习没有法律障碍；本项目"OO 重写 + snake_case 唯一写法 + typed + 300 测试 + 全局事件总线"的现代化差异化依然成立，且"免费替代"的紧迫性叙事让位于"现代化替代"。

### 3.2 FreeSimpleGUI —— 直系同类，定位参照物

- PSG4 社区分叉（spyoungtech 发起），LGPL3、零依赖、版本续至 5.3.0 仍活跃。
- **已把巨石拆成包结构**：16k 行 `__init__.py` + `elements/` 30 个文件（button/input/combo/table/graph/…/calendar）+ `window.py` + `tray.py`。
- API 完整保留 PSG4 契约（PascalCase 主 + snake_case 别名、read 轮询、`[[...]]` 布局、popup/UserSettings/SystemTray/Debugger）。
- **与本项目一句话**：它走"原版续命 + 保兼容"，本项目走"推倒重写 + 现代化"——它背 PSG 全部历史包袱，换来的是 PSG 用户零成本迁移；本项目换来 OO 干净分层与事件总线。
- README 对比表应把它放第一行。

### 3.3 CustomTkinter —— 现代外观标杆，实现手法宝库

- **绘制引擎**（`DrawEngine`，作者自述"一年实验"）：每个控件 = `CTkCanvas` + 内部 `tk.Label`（文字/图片）；圆角三种绘制策略按平台自动选：`polygon_shapes`（多边形）/ `font_shapes`（**字体字形当抗锯齿圆角**）/ `circle_shapes`；所有尺寸**强制取偶**防锯齿。
- **外观模式**：`AppearanceModeTracker` 全局单例 + darkdetect 30ms 轮询系统亮暗，颜色一律 `(light, dark)` 二元组。
- **DPI 缩放**：`ScalingTracker` 每窗口记 DPI 因子 + 100ms 循环，控件尺寸/字体全过 `_apply_widget_scaling`。
- 不足：布局零抽象、事件只有 command 回调、控件仅约 20 个、主题是巨大 json、维护放缓、社区靠外圈补件（CTkMenuBar/CTkTable/CTkMessagebox…）续命——补件又依赖 CTk 本体，生态碎片化。

### 3.4 ttkbootstrap 2.x —— 最活跃的正统库，激进转向

- 2.x 把门槛抬到 **≥3.10** 且 **Pillow 变硬依赖**——零依赖赛道上已无对手。
- **单 root 强制**：`Style` 进程单例绑死第一个 root，开第二个 root 直接 `RuntimeError`（`_require_single_root`）。本项目的"隐藏主 root 多窗口 + 全局总线"在生态里是独一份，应写进 README 作对比卖点。
- 值得抄的细节：**类级绑定白送全局行为**——`bind_class("TEntry", "<Control-a>")` 全选、`bind_class("TButton", "<Key-Return>")` Enter 触发默认按钮、disabled 态自动换光标。
- `theme_mode`/`toggle_theme`（亮暗双模式）、`on_close` 装饰器、`place_window_center()`、i18n 目录、随包发 ttkcreator 主题编辑器。
- 特色控件路线：`Meter` 用 **PIL 3 倍分辨率离屏渲染**拿抗锯齿——与本项目图表"Pillow 可选/矢量回退"双后端思路互相印证。
- 它的 `Publisher/Subscriber` 总线**只用于内部主题广播**，不开放给用户——本项目的事件总线仍是独有卖点。

### 3.5 pygubu —— "布局即数据"流派

- `.ui` XML + `Builder` 运行时加载 + designer 可视化编辑；资源池链式查找（`ChainedResourcePool`）、i18n translator 内建、插件机制甚至适配 CTk 控件。
- 不足：调试间接、动态布局别扭、需要装 designer 应用。
- **启发**：本项目的 list-of-lists 布局本来就是纯数据，加 `to_spec()/from_spec()`（dict/JSON）成本极低，即可拿到"布局可存文件/运行时生成"能力，无需 XML。

### 3.6 maliang —— 全 Canvas 自绘同类（理念浓度最高）

- 中文项目（Xiaokang2022），MIT、≥3.11、零依赖核心，1,102★，"所有 UI 画在 Canvas 上"。
- **虚拟元素树**：`Widget = N×(Shape/Text/Image) + 1×Style + 1×Feature`——外观元素可任意叠加，风格与功能混入各限一个，组合优于继承。
- **动画系统内建**：每个元素带 `gradient_animation`，任何颜色变化（悬停/主题切换/进度）走 `GradientItem` 平滑过渡而非瞬间重绘。
- **薄核心 + 官方子包**：maliang-mpl（matplotlib）/ maliang-media / maliang-three（3D）/ maliang-table；pywinstyles、darkdetect 收编为 optional extras。
- color 独立成包（HSL/RGB 转换）、theme manager、toolbox。

### 3.7 tukaan —— API 现代化的极致标本（已停更）

- MIT、≥3.7、167★。**属性描述符声明**：`class Button: text = TextProp(); action = CommandProp()`——类属性声明描述符协议，`button.text = "Hi"` 自动同步 Tcl，类型转换/setter/getter 全由 Prop 基类包办，比手写 property 省约 80% 样板。
- 结构现代：`a11y`（无障碍）、dialogs 全家（**colorpicker / fontpicker / datetimedialogs**）、fonts/fontfile、theming（kolorscheme/lookandfeel）、windows/wm、time/timeouts、clipboard/screen。
- **死因**：`libtukaan-win/unix/mac==0.1.2` 每平台一个原生二进制，维护不动——反面印证"纯 ctypes、零原生资产"铁律。

### 3.8 guizero / TKinterModernThemes / TkZero / appjar —— 教学与小众

- **guizero**（教学）：`grid=[x,y] + align` 参数化布局、`events.set_event` 命名事件；最值得学的是**报错体验**（错误消息带 `self.description` 定位到控件与参数）。
- **TKinterModernThemes**：tcl 主题（azure/sun-valley/park）+ 命令行参数 + `themeconfig.json` 双通道主题配置（有趣的细节）；WidgetFrame 布局助手。
- **TkZero**：纯 OO 属性式 API（`Vector.Size/Position`、Keybind、hover 跟踪），但停在 0.2.0——**教训：API 优雅救不了没有示例/文档/生态的库**。
- **appjar**：单文件巨石 + `addXxx` 系列方法 + **函数名字符串当回调**（`press("handleButton")`）——字符串化回调是明确反模式；已死多年。

---

## 四、理念专题（每条都可搬）

1. **颜色变化应该是动画，不是跳变**（maliang）。本项目的 `_paint` 主题切换/hover 全是瞬时跳变；加一个颜色 tween（几十行）是性价比最高的"质感跃升"。
2. **控件属性用描述符声明**（tukaan Prop）。本项目元素是显式 property 封装（每控件几十行样板），描述符协议可大幅瘦身；3.7 完全可用，注意与 `__slots__`/元类的组合。
3. **状态驱动回流（双向绑定）**（LayoutX Store / tkpf / tkmvvm）。本项目事件总线是"UI→代码"方向；缺"状态→UI"回流半边。不必上 Redux——一个 `bind_var(key, element)` 原语（内部走总线）即零依赖落地。
4. **运行时检查器**（formation-dbg）。附加到运行中的 Tk 应用实时检视/修改控件 + REPL，tkinter 界的浏览器 DevTools。本项目 todo 里"dbg 省略"可借鉴此形态：`ts.inspect(window)` 热检视器。
5. **薄核心 + 官方子包扩展**（maliang-mpl/-three/-table）。将来图表（最大的独立功能块）可拆可选子包的先例——零依赖核心不变。
6. **快照视觉回归测试**（Textual，圈外 TUI 但理念最富）。把本项目的人工截图目检自动化成"渲染固定场景 → 对比基线 PNG"的回归门，尤其适合自绘控件。
7. 圈外参照另两个：**DearPyGui**（IMGUI 即时模式——反证保留模式+声明式布局在桌面端是对的）；**Kivy KV**（绑定关系应可声明，而不总是命令式 update）。

---

## 五、关键发现汇总

1. **PySimpleGUI 6 重新开源（LGPL3）**——商业化 5.x 时代结束；本项目定位从"免费替代"转向"现代化替代"（OO/snake_case/typed/事件总线/300 测试）。LGPL3→GPL3 向上兼容，参照学习合法。
2. **文件拖放可以零依赖翻案**——windnd 纯 ctypes 实现：`DragAcceptFiles(hwnd)` + 拦截 `WM_DROPFILES(0x233)` + `SetWindowLong(GWL_WNDPROC)` 子类化窗口过程（32/64 位分支），零二进制扩展，与本项目 system_tray 裸调 Win32 同一套模式。todo.md ⛔ 清单"文件拖放（需 tkdnd 扩展）"的理由不再成立。windnd 自身代码质量差（`raise "字符串"`、模块 global 存状态），可行但不照抄。
3. **竞品门槛集体抬高**：ttkbootstrap 2.x ≥3.10 + Pillow 硬依赖；maliang ≥3.11；tukaan 死于原生二进制——**"3.7 下限 + 真零依赖 + 多窗口"是本项目独占的生态位**。
4. **单 root vs 多窗口**：ttkbootstrap 2.x 明确单 root（第二 root 直接 RuntimeError）；本项目隐藏主 root 多窗口 + 全局总线是差异化卖点，应写进 README。
5. **"拖放/WebView 必须 tkdnd/tkhtml 二进制"只对跨平台成立**：tkinterdnd2/tkinterweb 的实现都是"原生二进制打进 wheel"；Windows-only 场景纯 ctypes 可行（windnd、winotify 已验证）。
6. **图标字体的零依赖路线存在**：tkfontawesome 依赖 lxml+tksvg（SVG 路线）；零依赖应走内嵌 ttf 字形（如 segmdl2.ttf 的 Unicode 图标区段）——本项目自绘控件目前全靠几何形状画图标，这是可选增强。
7. **许可雷区**：ttkwidgets 是 AGPL（与 GPL 项目混用需按 §13 处理）；tksheet/tkcalendar 元数据未标注或 GPLv3——借鉴源码前先看许可。

---

## 六、行动建议清单（按性价比排序）

| # | 建议 | 理念来源 | 成本 | 说明 |
|---|---|---|---|---|
| 1 | **拖放翻案**：改 ⛔ 清单表述；实现 `window.drop_target(func)` | windnd | 低~中 | 纯 ctypes，与 system_tray 同基础设施 |
| 2 | **颜色渐变动画**：`_paint` 加颜色 tween | maliang | 中 | 主题切换/hover 平滑过渡，质感提升最大 |
| 3 | **DPI 缩放** | CustomTkinter `ScalingTracker` | 中 | `SetProcessDpiAwareness` + `tk scaling` + 尺寸钩子 |
| 4 | **三个标配对话框**：colorpicker/fontpicker/date | tukaan 形态 | 中 | popup 全家桶补缺 |
| 5 | **系统亮暗跟随 + DWM 美化** | CTk / pywinstyles | 中 | Windows 读注册表；暗色标题栏/Mica/圆角一行 ctypes |
| 6 | **类级绑定**：Ctrl+A 全选 / Enter 默认按钮 / 禁用光标 | ttkbootstrap | 低 | `window.py` 里一个小函数全局生效 |
| 7 | **`from_spec()`/`to_spec()` 布局序列化** | pygubu/Formation | 低 | 布局即数据是既有优势，补上序列化即新卖点 |
| 8 | **README 对比定位表**（FreeSimpleGUI/CTk/ttkbootstrap vs 本项目） | 本轮调研 | 低 | 把"多窗口+零依赖+3.7"写成对比卖点 |
| 9 | **双向绑定原语** `bind_var(key, element)` | tkpf/LayoutX | 中 | 挂在现有事件总线上 |
| 10 | **canvas 快照回归测试** | Textual | 中 | 把人工截图目检自动化为回归门 |
| 11 | 圆角抗锯齿（font_shapes / PIL 超采样） | CTk / ttkbootstrap Meter | 中 | `_paint` 可选增强 |
| 12 | 图标字体表（内嵌 ttf 字形） | tkfontawesome 反推 | 低 | 自绘控件的图标增强 |

---

## 七、附录

### 调研环境

- venv：`%TEMP%\tksg_survey_venv`（34 包），源码位于 `Lib\site-packages\`，可随时翻阅或整体删除。
- 元数据脚本：`%TEMP%\tksg_survey_meta.py`（importlib.metadata 打印版本/许可证/依赖/Python 下限）。

### 主要来源

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) ／ [官方文档](https://customtkinter.tomschimansky.com)
- [ttkbootstrap](https://github.com/israel-dryer/ttkbootstrap) ／ [文档](https://ttkbootstrap.readthedocs.io/en/latest/about)
- [PySimpleGUI](https://github.com/PySimpleGUI/PySimpleGUI) ／ [PyPI（LGPL3 声明）](https://pypi.org/project/PySimpleGUI/)
- [FreeSimpleGUI](https://github.com/spyoungtech/FreeSimpleGUI)（PyPI：FreeSimpleGUI）
- [pygubu](https://github.com/alejandroautalan/pygubu) ／ [pygubu-designer](https://github.com/alejandroautalan/pygubu-designer)
- [maliang](https://github.com/Xiaokang2022/maliang) ／ [tukaan](https://github.com/tukaan/tukaan) ／ [Formation](https://github.com/ObaraEmmanuel/Formation)
- [tkpf](https://github.com/marczellm/tkpf) ／ [LayoutX](https://github.com/Bomberus/LayoutX) ／ [tkmvvm](https://github.com/Joklost/tkmvvm)
- [rdbende 主题群](https://github.com/rdbende)（Sun Valley / Azure / Forest / tkinterDnD）
- [Akascape/py-window-styles](https://github.com/Akascape/py-window-styles) ／ [akascape.com/coding](https://www.akascape.com/coding)
- [PyUIBuilder（dev.to，2025）](https://dev.to/paul_freeman/my-python-gui-builder-just-crossed-300-stars-on-github-545h)
- [LibHunt：CustomTkinter vs TKinterModernThemes](https://www.libhunt.com/compare-CustomTkinter-vs-TKinterModernThemes)
- [ttk 主题列表（Tcler's Wiki）](https://wiki.tcl-lang.org/page/List+of+ttk+Themes)
- [Stackademic：2026 年该学哪个 GUI 库](https://blog.stackademic.com/which-python-gui-library-should-you-actually-learn-in-2026-9e49f9242cc8)
- [MLeidel/tkGUI 对比仓库](https://github.com/MLeidel/tkGUI)

### 未实装、凭生态常识提及（标注存疑）

PAGE、Tkinter-Designer、PyUIBuilder、DragDropTK、PythonIDE-PyMe（均为应用程序，非 pip 库）；
PMW（Python Mega Widgets，2000 年代经典 mega-widget 集合，已死，历史地位）；Tix（曾随 Python 打包后被移除——"C 扩展控件进标准库"的教训）。

---

## 八、补记：定位决策与已执行动作（2026-10-27）

报告完成后用户拍板：**不与 PySimpleGUI 兼容，不背历史包袱，历史残留与不良 API 全部舍弃**。
据此立即执行了兼容层剥离（详见 todo.md「剥离 PySimpleGUI 兼容层」一节）：删除 32 个遗产名
（`InputText`、`MsgBox`、`popup_quick` 族、`running_trinket/replit`、Translator/i18n 全家、
双拼哨兵常量、RELIEF_* 等），`list_of_look_and_feel_values`→`theme_list`、
`theme_add_new`→`theme_add`、`LOOK_AND_FEEL_TABLE`→`THEMES`，导出 `ts.settings` 单例，
测试 300→299 双解释器全绿。行动建议清单中第 8 项（README 对比定位表）的口径随之更新：
对上游的关系从"续命/替代"改写为"彻底独立"，FreeSimpleGUI 仍是同名概念最近邻，但不再构成约束。
