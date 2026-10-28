<h align="center">
  <img src="logo.png" alt="TkSimpleGUI" width="360">
</h>

# TkSimpleGUI

**TkSimpleGUI** 是一个纯 Tkinter/ttk 的 Python GUI 框架：Python 3.8+ 零第三方依赖
（3.7 需 `typing_extensions` 一个条件依赖）。声明式布局、面向对象控件、
全局事件总线、统一事件循环——用 Tk 也要有 Qt 的开发体验。

> 由 PySimpleGUI 4.x（GPLv3）分叉而来，现已是独立的框架：不再兼容上游 API，
> 全面转向「零事件循环 + 事件装饰器」的现代写法。改名是为了避免与
> PySimpleSoft 的商标冲突，同时如实反映项目的独立性。

---

## 特性

- **零事件循环** — 永远不写 `while True`：`window.run()` 一个入口，
  全局唯一事件循环天然支持多窗口协同
- **双向绑定** — `ts.Var` 可观察值容器 + `window.bind_var(key, var)`：
  写 var 扇出全部绑定元素，用户改动泵心跳回拉，跨窗口共享同一个 var
- **事件绑定走装饰器** — `@ts.bind_event` 绑定模块级 `on_*` 函数，
  `window` / `event` / `values` 按参数名自动注入
- **面向对象控件** — 每个控件都是真正的类实例，属性读写、方法直调，
  不再和 `window["-KEY-"].update(...)` 的字符串寻址缠斗
- **T 前缀命名** — 每个控件类一律以 T 开头（`ts.TText` / `ts.TInput` /
  `ts.TButton`），一眼即知是本框架控件，全库一个概念只有一个名字
- **消灭魔术字符串** — Tk 的字符串选项全部类型化为枚举
  （`ts.Anchor.CENTER`、`ts.Justify.RIGHT`、`ts.EventType.DOUBLE_CLICK`、
  `ts.Color.NAVY`、`ts.Relief.SUNKEN`…），枚举值本身就是 Tk 字符串，裸字符串依旧可用
- **dataclass 配置对象** — `ts.WindowConfig` / `ts.ElementOptions`
  声明式参数包，可共享复用
- **100% 类型标注** — `py.typed`（PEP 561），ty 零诊断，IDE 全程补全与检查
- **超越 Tk** — 圆角按钮、图像按钮、文字进度条、全局热键、任务栏进度、
  系统托盘、日历控件、表格编辑/排序、拆分器、流式面板……Tk/ttk 没有的这里也有
- **自绘展示控件** — Element Plus 风格的标签/徽章/头像/统计数值/空状态/结果页/
  步骤条/时间线/骨架屏/警告条/水印/描述列表/卡片/分段控制器/评分/分页器/穿梭框：
  全部 TCanvas 自绘或原生组合，随主题自动换色，零新依赖
- **日志直接进日志框** — `TOutput` 就是日志框：`out.log("...")` 一行落笔，
  级别配色（debug/info/success/warning/error）+ 时间戳 + 行数上限（环形缓冲）+
  可选文件镜像；`ts.log(...)` 一行式无对象写入，`Logger.attach_logging()`
  把标准 `logging` 桥接进来，工作线程写入也不会崩 Tk
- **封装彻底** — `__slots__` 全覆盖、私有属性 + `@property`、
  主题与设置走单例而非模块全局
- **系统原生外观** — 不调 `ts.theme()` 就不覆盖任何颜色，ttk 用操作系统原生主题
- **Python 3.7+** — 3.8+ 零第三方依赖（3.7 需 `typing_extensions`），Tkinter/ttk + 标准库

## 与同类库对比

同为 Tkinter 封装的主流方案，与 TkSimpleGUI 的横向对比
（数据来自各家官方文档 / PyPI，2026-10）：

| | **TkSimpleGUI** | FreeSimpleGUI | CustomTkinter | ttkbootstrap 2.x |
|---|---|---|---|---|
| 定位 | OO 重写的现代 Tk 框架 | PSG4 社区分叉（原版续命） | 现代外观控件集 | ttk 主题 + Bootstrap 观感 |
| 许可 | GPL-3.0-or-later | LGPL-3.0 | MIT | MIT |
| Python 下限 | **3.7** | 3.8+ | 3.8+ | **3.10+** |
| 第三方依赖 | **无**（3.7 需 typing_extensions） | 无 | darkdetect（可选） | **Pillow 硬依赖** |
| 编程范式 | 面向对象 + 全局事件总线 | 过程式 + read 轮询（PSG 契约） | 命令回调（无事件抽象） | ttk 主题 + 命令回调 |
| API 风格 | T 前缀 + snake_case 唯一写法，100% 类型标注 | PascalCase 主 + snake 别名（保 PSG 兼容） | `CTk` 前缀 | ttkbootstrap 前缀 |
| 多窗口 | **一等公民**：隐藏主 root + 全局总线，任意窗口间发事件 | read_all_windows 轮询 | 单窗口为主，多窗口手工管理 | **单 root 强制**，第二个 root 直接报错 |
| 布局 | `[[...]]` list-of-lists + pack/grid 抽象 | `[[...]]` list-of-lists | 无布局抽象（place 手工） | pack/grid 手工 |
| 控件数量 | 60+（含 17 个 Element Plus 风格自绘） | PSG4 全家桶（巨石拆包） | ~20 个（社区补件碎片化） | ttk 全量 + Meter 等增强 |
| 主题 | 5 套手工低饱和配色 + 原生观感（不调 theme 即系统默认） | PSG 主题表继承 | 亮/暗双模式 + json 主题 | Bootstrap 色系 + 主题编辑器 |
| 类型标注 | **py.typed，全量** | 部分 | 部分 | 部分 |
| 适合谁 | 要 OO/类型/多窗口/长维护的现代 Python 项目 | PSG4 老用户零成本迁移 | 只需要几个现代观感控件 | 喜欢 Bootstrap 观感、固定 3.10+ |

> 一句话：**FreeSimpleGUI 保 PSG 兼容、CustomTkinter 补观感、ttkbootstrap 给主题——
> TkSimpleGUI 把这些换成一个统一的现代 OO 框架**：事件总线、类型标注、多窗口、
> 零依赖、3.7 起步。

## 安装

```bash
pip install TkSimpleGUI
```

## 快速上手

```python
import TkSimpleGUI as ts

window = ts.Window("Demo", [
    [ts.TText("Hello, TkSimpleGUI!", key="-OUT-")],
    [ts.TInput(key="-IN-"), ts.TButton("Greet")],
    [ts.TButton("Exit")],
])

@ts.bind_event
def on_greet(window, values):
    window["-OUT-"].update(f"Hello, {values['-IN-'] or 'stranger'}!")

@ts.bind_event
def on_exit(window):
    window.close()

window.run()   # 就这一行——没有 while True
```

多窗口同样零仪式：

```python
main = ts.Window("Main", [[ts.TButton("Open child")], [ts.TButton("Quit")]])
child = ts.Window("Child", [[ts.TText("I am the child")], [ts.TButton("Close me")]],
                  parent=main)

@ts.bind_event
def on_open_child(window):
    child.un_hide()

@ts.bind_event
def on_close_me(window):
    window.close()

main.run()     # 唯一的循环，泵所有窗口
```

## 窗口层级

```python
main = ts.Window("Main", layout)
child = ts.Window("Child", layout, parent=main)

child.parent is main        # True
main.children               # [child]
child.is_child_of(main)     # True
child.close()               # 级联关闭自己的子窗口
```

## 双向绑定（ts.Var）

`ts.Var` 是可观察值容器，`window.bind_var(key, var)` 把元素键桥接到它——
写 var 扇出到全部绑定元素，用户改动在每个事件泵心跳回拉进 var，并复制到
同 var 的其他绑定元素（两个窗口共享同一个 var 也一样）：

```python
count = ts.Var(0)

window = ts.Window("计数器", [
    [ts.TButton("+1", key="-ADD-")],
    [ts.TInput("", key="-N-")],
    [ts.TText("", key="-ECHO-")],
], finalize=True)

window.bind_var("-N-", count)     # 输入框 ↔ var
window.bind_var("-ECHO-", count)  # 显示框 ← var（扇出目标）

count.value = 1                   # 输入框与显示框同时变 "1"
# 在输入框里打字 → 下一次泵 tick：count.value 更新，显示框跟着变

@ts.bind_event("-ADD-")
def on_add(window, values):
    count.value = int(count.value or 0) + 1

window.run()
```

绑定时 var 的值胜出（同 tk Variable 的直觉；`Var()` 默认 None 则不动元素，
首个泵 tick 采纳元素现值）。要求 finalize 后的窗口；绑定的元素其 `update()`
须接受 `value=`（与 `window.fill()` 同一契约）。解绑用 `window.unbind_var(key)`，
窗口关闭时自动解绑。

## 声明式配置（dataclass）

```python
import TkSimpleGUI as ts

label_style = ts.ElementOptions(justification=ts.Justify.CENTER,
                                expand_x=True, pad=(8, 4))

layout = [
    [ts.TText("Title", config=label_style)],
    [ts.TText("Body", config=label_style)],
]

cfg = ts.WindowConfig(title="Settings", size=(420, 280), resizable=True,
                      layout=layout)
window = ts.Window(config=cfg, finalize=True)   # 布局进 config，或直接 layout=
```

## 日志写进日志框（TOutput 控件）

`TOutput` 就是日志框，日志层直接长在它上面——没有第二个输出通道：

```python
log_box = ts.TOutput(size=(90, 12), key="-LOG-")

log_box.log("采样已启动")                     # INFO，主题字色
log_box.log("通道 3 噪声偏大", level="warning")  # 琥珀色
log_box.log("通道 7 断线", level="error")      # 与错误提示条同一个红

# 一行式：key 可省（默认取最新窗口里的第一个 TOutput）
ts.log("任意位置写一行", key="-LOG-")

# 需要更正式的日志：行数上限（环形缓冲）、文件镜像、标准 logging 桥接
logger = log_box.logger(max_lines=500, mirror="run.log")
logger.attach_logging("INFO")                 # logging.* 也进这个框
logging.getLogger("采集服务").warning("队列积压")  # → 12:03:44 WARNING 采集服务: 队列积压

# 工作线程里也能安全写（Logger 排队，回到 Tk 线程落笔）
def sample_channels():
    logger.info("开始采样")
    return "12 个通道"

window.start_task(sample_channels, end_key="-DONE-")

@ts.bind_event("-DONE-")
def on_done(window, values):
    result = values["-DONE-"]             # 成功=返回值；失败=异常对象
    if isinstance(result, BaseException):
        logger.error(f"采集失败：{result}")  # traceback 也会进 TkSimpleGUI.task
    else:
        logger.success(f"采集完成：{result}")
```

级别：`debug`（灰）/ `info`（主题字色）/ `success`（绿）/ `warning`（琥珀）/
`error`、`critical`（红）；每行自带时间戳（`timestamp="%H:%M:%S"`，可改可关），
`color=` 可按业务覆盖。找关键字用 `search_all()`，右键菜单可复制/清空。

## 目录结构

```
TkSimpleGUI/
├── src/TkSimpleGUI/            # 对象导向包（import TkSimpleGUI）
│   ├── __init__.py             # 公开 API（控件类一律 T 前缀）
│   ├── enums.py                # 13 类 Tk 字符串枚举（Anchor/Color/EventType…）
│   ├── config.py               # WindowConfig / ElementOptions dataclass
│   ├── _version.py             # 版本信息
│   ├── constants.py            # 不可变常量
│   ├── _theme_data.py          # 5 套手工主题表（含 System 原生）
│   ├── _theming.py             # ThemeManager（主题状态封装）
│   ├── _typing_compat.py       # 3.7 的 Literal 兼容层
│   ├── settings.py             # Settings 单例（全局选项封装）
│   ├── utils.py                # rgb、Timer、平台检测、DPI 感知
│   ├── event.py                # TkSimpleEvent 全局事件总线 + default_app
│   ├── actions.py              # Action / ActionList（Delphi TActionList 对标）
│   ├── user_settings.py        # UserSettings（JSON 持久化）
│   ├── animation.py            # fade/slide/progress 动画辅助
│   ├── hotkey.py               # 全局热键 + 任务栏进度（Win32/COM）
│   ├── input_blocker.py        # 系统级输入屏蔽（模态加强）
│   ├── popup.py                # 基于 Window 本体的弹窗族
│   ├── elements/
│   │   ├── base.py             # Element(ABC) + 右键菜单 + 网格布局引擎
│   │   ├── _paint.py           # 自绘控件的共享绘制/调色基础层
│   │   ├── widgets.py          # TText/TInput/TCombo/TListbox/TSpin/TCheckbox/TRadio…
│   │   ├── buttons.py          # TButton 及浏览/开关/图像变体
│   │   ├── fancy.py            # 圆角按钮/图像按钮/文字进度条/仪表盘/TLED
│   │   ├── media.py            # TImage/TCanvas/TGraph（图元句柄）
│   │   ├── containers.py       # TFrame/TColumn/TSplitter/TTabGroup/TToolbar…
│   │   ├── calendar.py         # 内嵌月历
│   │   ├── chart.py            # 图表（9 种类型 + 误差棒/参考线/直方图）
│   │   ├── display.py          # 标签/徽章/头像/统计/空状态/结果页/骨架屏/警告条/水印
│   │   ├── panels.py           # 卡片/描述列表/步骤条/时间线
│   │   ├── selection.py        # 分段控制器/评分/分页器/穿梭框
│   │   └── data.py             # TTable（排序/编辑/图标）、TTree
│   └── window/
│       ├── window.py           # Window：统一循环、层级、定时器、剪贴板
│       └── system_tray.py      # SystemTray（托盘图标/菜单/气泡/事件）
├── demos/                      # 演示脚本（feature showcase + 基本模板）
├── tests/test_package.py       # 测试套件（298 项，pytest/unittest 均可跑）
├── todo.md                     # 路线图
├── pyproject.toml
└── README.md
```

## 开发与测试

```bash
pip install -e .
python -m pytest tests -q             # 299 项测试（每测试 30s 超时守护）
python -m unittest discover tests     # 同一套测试的 unittest 跑法
python tests/check_types.py           # ty 类型检查守卫
python tests/check_syntax.py          # 3.7 语法门（用运行中解释器的 ast 解析全部 .py）
python demos/showcase.py --smoke      # showcase 冒烟自检
```

## 版本信息

- **Version**: 0.1.0
- **Python**: >= 3.7
- **License**: GPL-3.0-or-later（继承自上游 PySimpleGUI 4.x）
