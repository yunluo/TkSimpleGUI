# 日志→Output 控件 设计说明（2026-10-13）

> 目标读者：实现者。本文件是 API 契约，测试按本文写。

## 1. 需求

用户口径："我要的日志是显示到 output 模块控件"。即：日志的落点就是
`ts.Output`（只读 Multiline）这个控件本身，不要独立的日志窗口，不要强制
引入第三方日志系统。上游 PySimpleGUI 的 `Print`/`easy_print`（stdout 重定向）
在 OO 重写时没带过来，本批次补上"控件化日志"。

## 2. 现状（复用而非重造）

`Multiline`（[widgets.py]）已经提供了日志渲染需要的全部原语：

- `print(*args, text_color=...)` — 追加一行 + 原生 tk.Text tag 着色 + `see("end")` 自动滚到底
- `delete(first, last)` / `clear()` / `get()` / `insert()` / `see()`
- `search_all()` + `clear_highlights()` / `link()`（日志里找关键字、点链接）
- 主题跟随（`apply_theme`）、`scroll_y`、`wrap="none"`

`Output` 是它的只读子类。**本批次不新增渲染能力，只加"日志层"**。

## 3. 新增 API

### 3.1 `elements/widgets.py` 的 `Multiline` 扩展

```python
line_count -> int          # 当前行数（环形容量裁剪要用，本身也是常用查询）
logger(**options) -> Logger  # 该控件的 Logger；首次调用创建，options 只在创建时生效
log(*args, **kwargs) -> Multiline
    # = logger().write(*args, **kwargs)；kwargs: level / color / timestamp
```
- 新槽位 `_logger`（`Optional["Logger"]`，初值 None）；`Output.__slots__` 保持 `()`。
- `logger()` 里 `from ..logger import Logger` **惰性导入**（避免与包根/窗口模块的循环导入）。
- `line_count` 在控件未创建时返回 0。

### 3.2 新模块 `src/TkSimpleGUI/logger.py`

```python
class Logger(object):
    def __init__(self, element, timestamp="%H:%M:%S", max_lines=2000,
                 min_level="debug", colors=None, mirror=None, drain_ms=100)
```
- `element`：`Multiline` / `Output`（鸭子类型：用 `print`/`delete`/`line_count`/`widget`/`window`）。
- **级别**：`debug / info / success / warning / error / critical`，语义色沿用批次 A 的
  `_paint` 常量（与 Alert/Result 同一套语言）：
  `debug=INFO(#909399)`、`info=None`（控件自身主题字色）、`success=#67c23a`、
  `warning=#e6a23c`、`error/critical=#f56c6c`；`colors={level: color}` 可覆盖，
  单次调用的 `color=` 优先级最高（演示里按业务色写日志就靠它）。
- **行格式**：`f"{stamp}{LEVEL:<7} {message}"`；`timestamp` 为 `strftime` 格式串，
  `""`/`False` 关闭；单次调用 `timestamp=` 可覆盖格式或关闭。
- **方法**：`write(*args, level="info", color=None, timestamp=None)`、
  `debug/info/success/warning/error/critical(*args, **kwargs)`、`log(*args, **kwargs)`
  （`write` 的别名，读起来自然）、`clear()`、`flush()`、`close()`；
  属性 `element` / `lines` / `max_lines` / `level`。
- **环形上限**：`max_lines`（默认 2000，`None` = 不限）；每写一行后
  `overflow = line_count - max_lines`，`overflow > 0` 时 `element.delete("1.0", f"{overflow+1}.0")`。
- **文件镜像**：`mirror="app.log"`（追加、UTF-8、logger 持有并负责关闭）或任何带
  `write` 的对象（不接管关闭）；写纯文本（无 tag 着色），每行 flush。
- **线程安全**：写入线程 == 主线程 → 立即写；否则进 `queue.Queue`，由主线程上的
  定时器（`window.every(drain_ms)`，默认 100ms）批量排空。**定时器在 Logger
  构造时若窗口已就绪就启动**，否则在第一次主线程写入时补启动——所以
  "窗口 finalize 后创建 Logger / 在事件处理器里首次写日志" 是工作线程安全的前提
  （文档要写清）。`drain_ms=None` → 退化为仅主线程可用。
- **stdlib 桥接**：`attach_logging(level=None, name=None)` 往 `logging.getLogger(name)`
  挂一个内部 Handler（`%(name)s: %(message)s` 风格，非 root 时带 logger 名，
  `exc_info` 拼栈），并把该 logger 的级别调到 `level`（记住旧值以便 `detach_logging()`
  还原）；重复 attach 不叠加。`detach_logging()` 全部摘除。
- 窗口已关闭后写入：捕获 `tk.TclError` 静默丢弃（镜像文件仍然写），不崩。

### 3.3 一行式 `ts.log()`（包根导出）

```python
log(*args, key=None, level="info", color=None, window=None) -> bool
find_log_element(key=None, window=None) -> Optional[Multiline]
```
- 落点查找规则（文档明示）：给了 `key` → 该窗口里同 key 的元素（必须是 Multiline/Output）；
  没给 `key` → **最新打开**的窗口里第一个 Multiline/Output，逐个窗口往回找。
- 走 `element.log(...)`，即与 `Logger` 同一条代码路径（含环形上限与线程安全）。
- 找不到落点 → 返回 `False`（不抛），便于"日志框还没建好"的启动阶段调用。

### 3.4 `Window.elements` 公开属性

`-> Tuple[Element, ...]`：按布局顺序列出全部元素（含无 key 的）。日志查找
与用户自查都用它，避免外部代码摸 `_elements`。

## 4. 演示（showcase）

- `log()` 助手改为 `ts.log(text, key="-LOG-", color=color)`（时间戳由 Logger 统一加）。
- 日志面板旁加「logging 桥接」按钮：首次点击 `window["-LOG-"].logger().attach_logging(level="INFO")`，
  随后用 `logging.getLogger("工业采集").info/warning/error(...)` 打三条，验证桥接。
- smoke 路径补调该处理器。

## 5. 测试计划（~14 项，`TestLogger`）

1. `Output.log("x")` 写入一行、`get()` 含 `x` 且含 `[INFO]`？——格式断言：含级别标签与消息。
2. 时间戳：`Logger(element, timestamp=None)`/`timestamp=""` 关闭；自定义格式串生效。
3. 级别色：`level="error"` 的行 tag 前景 == `_paint.DANGER`（读 `_text.tag_names`/`tag_cget`）；
   `level="info"` 不加 tag（用控件默认色）。
4. `min_level="warning"` 过滤掉 info/debug，保留 warning/error。
5. 环形容量：`max_lines=3` 写 5 行 → `line_count == 3`，最早的消息消失，最后一条在。
6. 文件镜像：写到临时文件 → 内容含全部行且**不含** `#` 色值（纯文本）；`close()` 后可读。
7. `clear()` 清空；`lines` 属性与实际行数一致。
8. `attach_logging(level="INFO")` 后 `logging.getLogger("tksg-test").warning("hi")` 进日志框；
   `detach_logging()` 后再写不出现；attach 两次不重复。
9. 桥接级别：`attach_logging(level="WARNING")` 时 `info` 记录不出现、`warning` 出现。
10. 线程安全：工作线程 `logger.write(...)` × 5 → 泵 `window.read(timeout=...)` 直到
    `line_count == 5`，无异常。
11. `ts.log("hi", key="-LOG-")` → True 且内容可见；无落点时 → False。
12. `find_log_element()`：跳过硬编码 key 找最新窗口的 Output；指定 `window=` 时只看该窗口。
13. 主线程直接写（不经定时器）立即出现在 `get()` 里。
14. 窗口关闭后写入不抛异常。

## 6. 验证

五件套 + 双解释器（3.7.9 / 3.12）+ 日志面板截图目检（级别配色是否耐看）。
