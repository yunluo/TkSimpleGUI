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
- **事件绑定走装饰器** — `@ts.bind_event` 绑定模块级 `on_*` 函数，
  `window` / `event` / `values` 按参数名自动注入
- **面向对象控件** — 每个控件都是真正的类实例，属性读写、方法直调，
  不再和 `window["-KEY-"].update(...)` 的字符串寻址缠斗
- **两种命名风格** — 朴素（`ts.Text`）与统一 T 前缀
  （`ts.TText` / `ts.TInput` / `ts.TButton`）——同一个类，随你喜欢
- **消灭魔术字符串** — Tk 的字符串选项全部类型化为枚举
  （`ts.Anchor.CENTER`、`ts.Justify.RIGHT`、`ts.EventType.DOUBLE_CLICK`、
  `ts.Color.NAVY`、`ts.Relief.SUNKEN`…），枚举值本身就是 Tk 字符串，裸字符串依旧可用
- **dataclass 配置对象** — `ts.WindowConfig` / `ts.ElementOptions`
  声明式参数包，可共享复用
- **100% 类型标注** — `py.typed`（PEP 561），ty 零诊断，IDE 全程补全与检查
- **超越 Tk** — 圆角按钮、图像按钮、文字进度条、全局热键、任务栏进度、
  系统托盘、日历控件、表格编辑/排序、拆分器、流式面板……Tk/ttk 没有的这里也有
- **封装彻底** — `__slots__` 全覆盖、私有属性 + `@property`、
  主题与设置走单例而非模块全局
- **系统原生外观** — 不调 `ts.theme()` 就不覆盖任何颜色，ttk 用操作系统原生主题
- **Python 3.7+** — 3.8+ 零第三方依赖（3.7 需 `typing_extensions`），Tkinter/ttk + 标准库

## 安装

```bash
pip install TkSimpleGUI
```

## 快速上手

```python
import TkSimpleGUI as ts

window = ts.Window("Demo", [
    [ts.Text("Hello, TkSimpleGUI!", key="-OUT-")],
    [ts.Input(key="-IN-"), ts.Button("Greet")],
    [ts.Button("Exit")],
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
main = ts.Window("Main", [[ts.Button("Open child")], [ts.Button("Quit")]])
child = ts.Window("Child", [[ts.Text("I am the child")], [ts.Button("Close me")]],
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

## 声明式配置（dataclass）

```python
import TkSimpleGUI as ts

label_style = ts.ElementOptions(justification=ts.Justify.CENTER,
                                expand_x=True, pad=(8, 4))

layout = [
    [ts.Text("Title", config=label_style)],
    [ts.Text("Body", config=label_style)],
]

cfg = ts.WindowConfig(title="Settings", size=(420, 280), resizable=True)
window = ts.Window(config=cfg)
window.layout(layout).finalize()
```

## 目录结构

```
TkSimpleGUI/
├── src/TkSimpleGUI/            # 对象导向包（import TkSimpleGUI）
│   ├── __init__.py             # 公开 API + T 前缀别名
│   ├── enums.py                # 13 类 Tk 字符串枚举（Anchor/Color/EventType…）
│   ├── config.py               # WindowConfig / ElementOptions dataclass
│   ├── _version.py             # 版本信息
│   ├── constants.py            # 不可变常量
│   ├── _theme_data.py          # 生成式主题表（160 主题）
│   ├── _theming.py             # ThemeManager（封装的 look & feel）
│   ├── settings.py             # Settings 单例 + set_options/get_options
│   ├── utils.py                # rgb、Timer、平台检测、DPI 感知
│   ├── event.py                # TkSimpleEvent 全局事件总线 + default_app
│   ├── actions.py              # Action / ActionList（Delphi TActionList 对标）
│   ├── user_settings.py        # UserSettings（JSON 持久化）
│   ├── i18n.py                 # 字典翻译（Qt tr() 对标）
│   ├── animation.py            # fade/slide/progress 动画辅助
│   ├── hotkey.py               # 全局热键 + 任务栏进度（Win32/COM）
│   ├── popup.py                # 基于 Window 本体的弹窗族
│   ├── elements/
│   │   ├── base.py             # Element(ABC) + 右键菜单 + 网格布局引擎
│   │   ├── widgets.py          # Text/Input/Combo/Listbox/Spin/Checkbox/Radio…
│   │   ├── buttons.py          # Button 及浏览/开关/图像变体
│   │   ├── fancy.py            # 圆角按钮/图像按钮/文字进度条
│   │   ├── media.py            # Image/Canvas/Graph（图元句柄）
│   │   ├── containers.py       # Frame/Column/Splitter/TabGroup/Toolbar…
│   │   ├── calendar.py         # 内嵌月历
│   │   ├── data.py             # Table（排序/编辑/图标）、Tree
│   │   └── misc.py             # StatusBar/Separator/Sizegrip
│   └── window/
│       ├── window.py           # Window：统一循环、层级、定时器、剪贴板
│       └── system_tray.py      # SystemTray（托盘图标/菜单/气泡/事件）
├── demos/                      # 演示脚本（feature showcase + 基本模板）
├── tests/test_package.py       # 测试套件（188 项，pytest/unittest 均可跑）
├── todo.md                     # 路线图
├── pyproject.toml
└── README.md
```

## 开发与测试

```bash
pip install -e .
python -m pytest tests -q             # 188 项测试（每测试 30s 超时守护）
python -m unittest discover tests     # 同一套测试的 unittest 跑法
python tests/check_types.py           # ty 类型检查零诊断守卫
python demos/showcase.py --smoke      # showcase 冒烟自检
```

## 版本信息

- **Version**: 0.1.0
- **Python**: >= 3.7
- **License**: GPL-3.0-or-later（继承自上游 PySimpleGUI 4.x）
