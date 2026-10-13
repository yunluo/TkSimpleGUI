# 批次 A 设计说明：17 个自绘展示控件（Element Plus 对照）

> 目标读者：实现者（人或 agent）。本文件既是设计记录，也是逐元素的 API 契约；
> 实现必须与本文一致，测试按本文写。

## 1. 背景

对照 Element Plus 74 个组件盘点了 TkSimpleGUI 的缺口（见会话分析），其中 17 个
属于"纯绘制 + 状态"型：不需要弹层、不需要 Web 渲染能力，用 Canvas 自绘或既有元素
组合即可做到位，风险最低。本批次全部落地，并统一视觉语言（胶囊 / 描边卡片 /
语义色四态），顺带强化主题系统。

## 2. 通用约定（全部新元素适用）

- **Python 3.7 语法底线**：禁止海象 `:=`、`f(a, /, b)`、`list[int]` 内建泛型；
  用 `typing.List` 等。零参 `super()`。禁止 `except ImportError`（用 `except Exception`）。
- **代码全英文**：注释、docstring、类名、参数名、默认文案一律英文；非 ASCII 的
  `.py` 文件必须带 `# -*- coding: utf-8 -*-`（本批次文件应做到纯 ASCII，故通常不需要）。
- **ruff**：`line-length = 100`，规则集 `E,F,W,B,UP,SIM,PIE,RET,C4,PL,N`（`PLR0913`
  超参不报、`N` 命名不宽松）。新文件不得引入 `# noqa`（`_paint.py` 里的 UP032 除外）。
- **ty 零诊断**：`D:/bin/ty.exe check src --python-version 3.7` 必须全空。所有
  `__init__` 里初始化为 `None` 的槽位，用 **类级注解 + Optional** 声明：
  ```python
  _bar_id: Optional[int]
  ```
  并在 `__init__` 里赋 `None`。不要用 `# ty: ignore` 除非别无他法。
- **`__slots__`**：每个类必须声明 `__slots__` 元组，包含**全部**实例属性
  （类级注解不创建槽位）。守卫测试 `TestPy37Compatibility.test_slots_encapsulation`
  检查 `hasattr(el, "__dict__") is False`。
- **构造参数签名顺序**：`(业务参数..., key=None, tooltip=None, visible=True,
  pad=None, expand_x=False, expand_y=False, right_click_menu=None, metadata=None)`，
  与既有元素一致（见 `widgets.py::Text`）。
- **必须实现 `update()`**：基类 `Element.update` 抛 `NotImplementedError`。
  `update(xxx=None, ..., visible=None)` 语义：`None` = 不变；`visible` 走
  `self.unhide() if visible else self.hide()`；返回 `self`。
- **必须实现 `get()`**：返回值进入窗口 `values` 字典，异常被窗口吞掉（返回 None）。
- **必须实现 `apply_theme()`**：`import` 方式用 `from .. import _theming as theme_mod`；
  重算主题派生色并重绘。**显式色优先**：用户传了 `tag_color` 就永远用它，
  主题切换只影响未显式指定的部分。实现方式推荐"每次 `_draw()` 都从
  `_paint.palette()` 现取"，比 fancy.py 的 `_theme_xxx` 标志位更简洁。
- **事件**：`self._post_event()` 会投递 `self._key`（key 为 None 时投递 None，
  无害）。带载荷时用元组，格式与 `data.py::Table` 一致：`self._post_event((self._key, "close"))`。
- **绘制基础设施**：一律用 `_paint.py`（见第 3 节），不要再复制圆角/混色代码。
- **canvas 元素统一模式**：
  ```python
  def _create_widget(self, master):
      width, height = self._geometry()
      colors = _paint.palette(master, self._background_color)
      canvas = _paint.themed_canvas(master, width, height, colors["surface"])
      self._draw(canvas)
      return canvas

  def apply_theme(self):
      if self._widget is not None:
          self._widget.delete("all")
          self._draw(self._widget)
      return self
  ```
  `_draw(canvas)` 内部始终现取 `palette(canvas, ...)`，并 `delete("all")` 前先
  `self._widget.configure(background=colors["surface"])`（重绘时背景也要跟主题）。

## 3. 共享基础 `elements/_paint.py`（已实现，直接用）

| API | 说明 |
| --- | --- |
| `palette(widget, surface=None, ink=None) -> Dict[str,str]` | 解析当前主题为可用十六进制色：`surface / ink / muted / accent / accent_ink / border / track / subtle`。native 主题下采样平台默认色并用 `winfo_rgb` 归一化，所以永远返回可混合的 hex |
| `blend(color, other, ratio)` | 把 `color` 向 `other` 混合 `ratio`（0..1）。非 hex 输入原样返回 |
| `tint(color, colors, ratio=0.86)` | 颜色的"浅底"：`blend(color, colors["surface"], ratio)` |
| `shade(color, colors, ratio=0.30)` | 颜色的"深字"：`blend(color, colors["ink"], ratio)` |
| `status_color(status, colors)` | `info/success/warning/error/danger/primary` → 语义色（primary=accent） |
| `INFO/SUCCESS/WARNING/DANGER` | `#909399 / #67c23a / #e6a23c / #f56c6c` |
| `themed_canvas(master, w, h, surface)` | 无高亮框的平底 canvas |
| `rounded_polygon(canvas, x0,y0,x1,y1, radius, **kw)` | 圆角矩形（smooth 多边形） |
| `capsule(canvas, x0,y0,x1,y1, **kw)` | 胶囊（半径=半高） |
| `cross(canvas, cx, cy, size, **kw)` | "×" 两条线，返回 id 列表 |
| `check_mark(canvas, cx, cy, size, **kw)` | "✓" 折线，返回 id |
| `triangle(canvas, cx, cy, size, direction="up", **kw)` | 涨跌箭头 |
| `star_points(cx, cy, outer, inner, points=5, rotation=90)` | 星形顶点（屏幕坐标，首点在正上方） |
| `clip_left_half(points, limit=None)` | 多边形左半裁剪（Sutherland-Hodgman）；`limit` 默认取包围盒中线 → 正好是星形的一半 |
| `flatten(points)` | `[(x,y),…]` → `[x,y,x,y,…]` |
| `measure_text(widget, text, font)` | 像素宽（含 CJK），失败时 `len*8` 兜底 |
| `pil_modules()` | 可选 Pillow 探测 `(Image, ImageDraw)` 或 `False`（缓存，与图表后端共用） |
| `system_font_file(family=None)` | Pillow 用字体文件路径，找不到返回 `None` |
| `to_hex(widget, color, fallback)` | 任意 Tk 颜色名 → `#rrggbb` |
| `as_float(value, fallback)` | 安全转 float |

## 4. 逐元素契约

### 4.1 `elements/display.py`

#### Tag — 标签胶囊
```python
Tag(text, size=None, tag_color=None, text_color=None, effect="light",
    closable=False, font=None, key=None, enable_events=False,
    tooltip=None, visible=True, pad=None, expand_x=False, expand_y=False,
    right_click_menu=None, metadata=None)
```
- 几何：高 = `size[1] or 22`；文字内边距左右各 10；`closable` 时右侧多 18px 给 "×"（`cross`，size=8，中心距右边 9px、垂直居中）；宽 = `size[0] or max(40, text_w + 20 + (18 if closable else 0))`。
- 配色（`color = tag_color or palette["accent"]`）：
  - `effect="light"`（默认）：底 `tint(color, colors, 0.88)`，字 `shade(color, colors, 0.30)`，无描边。
  - `effect="dark"`：底 `color`，字 `theme_mod.contrast_on(color)`。
  - `effect="plain"`：底 `surface`，描边 `tint(color, colors, 0.55)`（宽 1），字 `shade(color, colors, 0.30)`。
  - `text_color` 显式时覆盖字色。
- 交互：点本体 → `enable_events` 时 `_post_event()`；点 "×" → `self.hide()` 且 key 非空时 `_post_event((self._key, "close"))`。
- `get()` 返回文本（关闭后仍返回文本）。`update(value=None, tag_color=None, text_color=None, visible=None)`：`value` 改文本并重绘，**同时 `unhide()`**（重新显示一个已关闭的标签）。

#### Badge — 徽章角标
```python
Badge(value=None, max_value=99, is_dot=False, badge_color=None,
      text_color=None, size=None, font=None, key=None, enable_events=False, ...)
```
- `value=None` → 空 canvas（尺寸仍为 1x1 还是给定尺寸：用 `size` 或 (1,1)）。
- `is_dot=True` → 直径 = `size[1] or 10` 的实心圆（忽略 value 的文本）。
- 数字：高 = `size[1] or 18`；文本 = `str(int(value))`，超过 `max_value` 时 `f"{max_value}+"`；宽 = `max(高, text_w + 10)`；胶囊 + 居中字（font 默认 `("TkDefaultFont", 8, "bold")`）。
- 颜色：底 = `badge_color or DANGER`（语义红，可覆盖）；字 = `text_color or contrast_on(底)`。
- `get()` → value；`update(value=None, is_dot=None, visible=None)`；`clear()` → value=None 并清空重绘。

#### Avatar — 头像
```python
Avatar(text=None, filename=None, data_base64=None, size=40, shape="circle",
       background_color=None, text_color=None, font=None, key=None,
       enable_events=False, ...)
```
- `size`：int 或 `(w, h)`，默认 40×40。
- **图片路径**：加载 `tk.PhotoImage`；有 Pillow 时用 `Image.new + mask(圆形) + ImageTk.PhotoImage` 做真圆裁剪（`ImageTk` 不可用或 Pillow 缺失 → 退化为居中平铺原图 + 画一圈描边表示形状）。
- **文字路径**（无图片时）：底 = `background_color or palette["accent"]`；字 = `text_color or contrast_on(底)`；字体默认 `("TkDefaultFont", int(min(w,h)*0.40), "bold")`；`shape="circle"` 画圆，`"square"` 画 `rounded_polygon`（半径 = min(w,h)*0.12）。
- 文字取前 2 个字符（EP 风格）。
- `get()` → text；`update(text=None, filename=None, data_base64=None, visible=None)`。

#### Statistic — 统计数值
```python
Statistic(label, value=0, prefix="", suffix="", precision=None, trend=None,
          trend_color=None, size=(170, 70), font=None, label_font=None,
          label_color=None, value_color=None, key=None, ...)
```
- 版面：label 在左上（anchor w，位置 (0, 4)，字 `label_font or ("TkDefaultFont", 9)`，色 `label_color or colors["muted"]`）；大数字基线在底部：`y = height - 10`，anchor `sw`，字号 `font or ("TkDefaultFont", 22, "bold")`，色 `value_color or colors["ink"]`。
- `precision`：小数位（`None` → 整数省略小数点，非整数用 `{:g}`）。
- 数值文本 = `f"{prefix}{formatted}{suffix}"`，但 prefix/suffix 用**小号字**（12）分别画在数字左右（同一基线、各 anchor 对齐）——实现方式：先量出三段宽度再依次排布。
- `trend`：`None / "up" / "down" / 数字`。数字 → 正=up、负=down，箭头右侧再画 `f"{abs(trend):g}%"`；符号 → 只画箭头。色 = `trend_color or (SUCCESS if up else DANGER)`；箭头用 `triangle`（size=8）。
- `get()` → value（原始数值）；`update(value=None, label=None, trend=None, prefix=None, suffix=None, visible=None)`。

#### Empty — 空状态
```python
Empty(text="No data", size=(160, 110), font=None, text_color=None,
      icon_color=None, filename=None, data_base64=None, key=None, ...)
```
- 默认：居中上方画一个"折角文档"图标（`rounded_polygon` 轮廓 + 折角多边形，线宽 2，色 = `icon_color or colors["track"]` 再 `blend(..., colors["ink"], 0.72)`）；下方居中画说明文字（`font or ("TkDefaultFont", 9)`，色 = `text_color or colors["muted"]`）。
- 给了 `filename/data_base64` → 用图片替代图标（PhotoImage，居中）。
- `text=""` → 不画文字。
- `get()` → text；`update(value=None, visible=None)`。

#### Result — 结果页
```python
Result(title, subtitle=None, status="info", size=(300, 200), icon_color=None,
       title_color=None, font=None, key=None, ...)
```
- 圆：半径 = `min(width*0.12, 30)`，圆心 `(width/2, 半径 + 14)`；填充 = `icon_color or status_color(status, colors)`。
  - `success` → 圆内 `check_mark`（size = 半径*1.0，色 `contrast_on(圆色)`，宽 3）
  - `error` → `cross`（size = 半径*0.8）
  - `warning` → 文字 "!"；`info` → 文字 "i"（`("TkDefaultFont", int(半径*0.95), "bold")`）
- 标题：居中，`y = 圆底 + 18`，`("TkDefaultFont", 15, "bold")`，色 `title_color or colors["ink"]`。
- 副标题：居中，标题下方 +8，`("TkDefaultFont", 9)`，色 `colors["muted"]`，`width=width-40` 自动换行（canvas text 的 `width=`）。
- `get()` → title；`update(title=None, subtitle=None, status=None, visible=None)`。
- 底部按钮行由用户自己在布局里加 `Button`（不做 slot）。

#### Skeleton — 骨架屏
```python
Skeleton(rows=3, animated=True, avatar=False, size=None, bar_height=14,
         gap=10, key=None, ...)
```
- 宽 = `size[0] or 240`；高 = `size[1] or rows*bar_height + max(rows-1,0)*gap`（`avatar=True` 时至少 40）。
- `avatar=True`：左侧直径 `min(40, height)` 的圆；条状区域右移（圆直径 + 12）。
- 条：`capsule`，最后一根宽 60%（`rows>1` 时），其余满宽。
- 基色 = `blend(colors["ink"], colors["surface"], 0.90)`；脉冲色 = `blend(colors["ink"], colors["surface"], 0.80)`；`animated=True` 时每 550ms 在两色间切换（`self._window.every(550, self._pulse)`，句柄存槽位）。
- `stop_animation()` / `start_animation()`；`_pulse` 里 `self._widget is None` 直接返回。
- `get()` → rows；`update(rows=None, animated=None, visible=None)`。

#### Alert — 内嵌警告条
```python
Alert(text, type="info", title=None, closable=True, show_icon=True,
      effect="light", size=(None, None), font=None, text_color=None,
      key=None, enable_events=False, ...)
```
- 组件树：`tk.Frame(highlightthickness=1, highlightbackground=边框色, background=底色)`
  → grid：`[icon canvas 18×18] [文字区] [close canvas 16×16]`，内边距 `padx=10, pady=6`。
- 底色：`effect="light"` → `tint(color, colors, 0.90)`；`"dark"` → `color`。
  边框：light → `tint(color, colors, 0.62)`；dark → `blend(color, "#000000", 0.15)`。
  文字：light → `colors["ink"]`（`text_color` 覆盖）；dark → `contrast_on(color)`。
- 图标：小圆填 `color` + 内部 "i/!/(✓/×)" 字样（`("TkDefaultFont", 8, "bold")`，色 `contrast_on(color)`）；`success`→"✓" `check_mark`，`error`→"×" `cross`。
- 文字区：`title` → 加粗 Label（`("TkDefaultFont", 10, "bold")`），描述 Label 在下（`font or ("TkDefaultFont", 9)`）；`size[0]` 给了就设 `wraplength=size[0]-70`。两个 Label 的 `background` 必须等于底色，`foreground` 等于字色。
- `closable` → 点 "×"：`self.hide()`，key 非空时 `_post_event((self._key, "close"))`。
- 点本体且 `enable_events` → `_post_event()`。
- `get()` → text；`update(text=None, title=None, type=None, visible=None)`。`apply_theme` 需重刷 frame/两 Label/canvas 三处颜色。

#### Watermark — 水印
```python
Watermark(text, size=(400, 260), font=None, color=None, gap=(140, 90),
          angle=-30, key=None, ...)
```
- 颜色 = `color or blend(colors["ink"], colors["surface"], 0.86)`（画布已知底色，用混色代替 alpha）。
- `angle == 0` → 直接在网格点 `create_text` 平铺（anchor "center"）。
- `angle != 0` 且有 Pillow 且 `system_font_file()` 命中 → 渲染一块 RGBA 文字贴片、`rotate(angle, expand=True, resample=BICUBIC)`、在 `surface` 底色上平铺，`ImageTk.PhotoImage` 贴成单个 image item。任一条不满足 → 静默退化为水平平铺（docstring 说明）。
- `get()` → text；`update(value=None, visible=None)`。
- docstring 需说明：Tk 的子控件不透明，水印画在自身 canvas 上，请放在它应覆盖的空白区域（或用 `expand_x/expand_y` 填满一个 Frame）。

### 4.2 `elements/panels.py`

#### Card — 卡片
```python
Card(title=None, layout=(), subtitle=None, extra=None, size=(None, None),
     background_color=None, border_color=None, padding=12, font=None,
     key=None, tooltip=None, visible=True, pad=None, expand_x=False,
     expand_y=False, justification=None, right_click_menu=None, metadata=None)
```
- 继承 `ContainerElement`；`_create_widget` 返回**最外层** `tk.Frame`（`highlightthickness=1`，`highlightbackground=border or palette["border"]`，`background=底`）。
- 内部结构（grid）：row0 = 头部 Frame（`title` Label 加粗 ink + `subtitle` Label 小号 muted 纵向排列；`extra` 元素 grid 在右侧 `sticky="e"`），row1 = 1px 分隔线 Frame（仅当有头部时，色 = border），row2 = `self._body` Frame。
- 头部与 body 的 `padx/pady = padding`（body 只留左右下）。
- **覆盖 `_post_create`**：不要调 `super()`（那会把 layout 建到最外层），改为把 `self._layout` 建到 `self._body`，并把 `extra` 注册 + `_build` + `_grid_into(self._header, 0, 1, ...)`（`_grid_into(master, row, column, default_pad, default_justification)`）。
- `size[0]` 给了 → `self._widget.configure(width=int(size[0]))`。
- `get()` → title；`update(title=None, subtitle=None, visible=None)`。
- `apply_theme`：重刷外层底色/描边、头部两 Label、分隔线色、body 底色。
- docstring 说明：Tk 无投影，卡片以 1px 描边 + 分层底色表达。

#### Descriptions — 描述列表
```python
Descriptions(items, columns=2, bordered=False, label_width=None,
             label_suffix="", font=None, label_color=None, text_color=None,
             size=(None, None), key=None, ...)
```
- `items`：`[(label, value), ...]` 或 dict（3.7 保序）。
- 组件树：`tk.Frame` + grid；每行放 `columns` 组"标签/值"对（`label_suffix` 拼在标签后，如 `":"`）。
- 标签 `ttk.Label`（`foreground=label_color or colors["muted"]`，`anchor="w"`，`width=label_width` 时用字符宽）；值 `ttk.Label`（`foreground=text_color or colors["ink"]`，`anchor="w"`）。
- `bordered=True`：外层 frame `highlightthickness=1` + `highlightbackground=border`，单元格 `padx=10, pady=6`；否则 `padx=0, pady=2`（值与标签间距 12）。
- `get()` → `{label: value}` dict；`update(items=None, visible=None)` → 重建子控件（先 `destroy` 旧子件）。
- `apply_theme`：重刷 frame 底色/描边 + 每个 Label 的前景色与背景。

#### Steps — 步骤条
```python
Steps(items, active=0, direction="horizontal", status="process", size=None,
      font=None, key=None, ...)
```
- `items`：`["Done", ("Step 2", "Details"), ...]`（str 或 (title, description)）。
- **horizontal**（默认）：圆直径 18，圆心 y = 16；每项单元格宽度 = `(size[0] or 计算值) / n`，`计算值 = n * max(96, max(量(title), 量(desc)) + 28)`；
  - 连接线：从 `cx_i + 11` 到 `cx_{i+1} - 11`（y=16），宽 2，色 = `accent if i < active else track`；
  - 标题：`(cx, 36)` anchor "n"，`("TkDefaultFont", 9)`，已完成的用 ink，未到的用 muted；
  - 描述：`(cx, 52)` anchor "n"，`("TkDefaultFont", 8)`，muted，`width=cell-10` 换行；默认高 70。
- **vertical**：圆心 x = 10，`y_i = i*row_h + 12`；`row_h = 64`；竖线 `(10, y_i+11) → (10, y_i+row_h-11)`；
  - 标题 `(26, y_i - 2)` anchor "w"；描述 `(26, y_i + 16)` anchor "w"（`width=width-40`）；默认高 = `n*row_h`，宽 300。
- 圆的状态（`i < active` → finish；`i == active` → `status`；`i > active` → wait）：
  - `finish` → 填 accent + `check_mark`（size 9，色 `accent_ink`）
  - `process` → 填 accent + 序号（`accent_ink`）
  - `error`/`danger` → 填 DANGER + `cross`（size 8）
  - `wait` → 填 surface + 描边 track（宽 1.5）+ 序号（muted）
- `get()` → active；`update(active=None, status=None, items=None, visible=None)`。

#### Timeline — 时间线
```python
Timeline(items, size=None, row_height=None, font=None, line_color=None, key=None, ...)
```
- `items` 元素可为：`str`（仅内容）/ `(timestamp, content)` / `{"timestamp":…, "content":…, "type":…, "color":…}`。
- 每项：竖线（x=8，从首圆到末圆，色 = `line_color or colors["track"]`，宽 1.5）；圆点 `create_oval` r=3.5，色 = `color or status_color(type or "primary", colors)`（type 缺省 `"primary"`）。
- 有 timestamp：小号 muted 一行（`("TkDefaultFont", 8)`，位置 `(20, y)` anchor "nw"），内容在其下 +14（`("TkDefaultFont", 9)`，ink，`width = width - 40` 换行）；`row_height` 默认 46（无 timestamp 时 30）；内容换行可能超高——用 canvas 的 `bbox` 计实际高度后推进 y（推荐：先 `create_text` 再 `bbox(item)` 量高）。
- 宽 = `size[0] or 320`；高 = `max(40, 最后一项 bbox 底 + 8)`（`size[1]` 给了就用它，画布固定尺寸时内容可能被裁剪，docstring 说明）。
- `get()` → `[(timestamp, content), ...]`；`update(items=None, visible=None)`。

### 4.3 `elements/selection.py`

#### Segmented — 分段控制器
```python
Segmented(options, default_value=None, size=None, font=None, key=None,
          enable_events=True, readonly=False, tooltip=None, visible=True, ...)
```
- `options`：`["Day", "Week"]` 或 `[("Day", "d"), ("Week", "w")]`（label, value）。
- 值 = 选中项的 value（纯字符串列表时 value = 字符串本身）。
- 几何：每项宽 = `measure(label) + 24`（最小 40）；高 = `size[1] or 30`；总宽 = `sum(项宽) + 4`；`size[0]` 给了 → 各按比例放大填满。
- 轨道：`capsule`，底 = `colors["subtle"]`，描边 `colors["border"]`（宽 1）；选中药丸：`capsule` 内缩 2px，底 = accent，字 = `accent_ink`；未选中字 = ink（hover → accent）。
- 交互：点击选中（变化时 `_post_event()`）；`readonly=True` 禁用；hover 高亮需要 `<Motion>`/`<Leave>`；键盘：canvas `takefocus=1`，点击后 `focus_set()`，`<Left>/<Right>` 移动选中并投递事件，选中态画 1px accent 外框表示焦点。
- `get()` → 当前 value；`update(value=None, options=None, visible=None)`（options 变化时保留仍在列表中的值，否则回退首项）。

#### Rate — 评分
```python
Rate(max_value=5, default_value=0, allow_half=True, size=None, colors=None,
     font=None, key=None, enable_events=True, readonly=False, ...)
```
- `colors` = `(filled, empty)`，默认 `("#f7ba2a", palette["track"])`。
- 星尺寸 = `size[1] or 26`；外半径 = 星尺寸/2，内半径 = 外半径*0.42；间距 = 星尺寸*0.28；画布宽 = `max_value*(星尺寸+间距) - 间距`，高 = 星尺寸。
- 星 = `star_points` + `create_polygon`；整星填 filled，空星填 empty。
- 半星（`allow_half`）：`clip_left_half(顶点)` + `flatten` 画左半（filled），右半单独画空星底面。
- 交互：`<Motion>` 预览（hovered = 星序号；`allow_half` 且 x 在星中心左侧 → +0.5）；`<Leave>` 还原；点击设置值（变化时 `_post_event()`）；`readonly=True` 无 hover 无点击。
- 点击第一颗星左半 → 0.5（不做"清除"语义）。
- `get()` → float 值；`update(value=None, max_value=None, readonly=None, visible=None)`。

#### Pagination — 分页器
```python
Pagination(total, page_size=10, current_page=1, pager_count=5,
           show_total=False, total_text="Total {total}", size=None, font=None,
           key=None, enable_events=True, ...)
```
- `page_count = max(1, ceil(total / page_size))`（数学上界；`page_size<1` 抛 `ValueError`，`total<0` 抛 `ValueError`）。
- 页码窗口算法（可测）：`page_count <= pager_count` → 全显示；否则
  `window_start = clamp(current - (pager_count-3)//2, 2, page_count - (pager_count-2))`，
  保留 `1` 与 `page_count`，中间显示 `[window_start, window_start + pager_count - 2)`，
  间隔 > 1 处插 `"…"`（间隔正好 1 时直接显示那个页码）。
- 按钮：高 = `size[1] or 28`，宽 = `max(28, 量(文本)+16)`；当前页 = accent 底 + accent_ink 字；其他 hover = subtle 底；prev/next 用 "‹" "›" 字形；首页时 prev 与末页时 next 用 muted 且不可点。
- `show_total=True` → 左侧画 `total_text.format(total=total)`（muted）。
- 点击 → 换页（变化时 `_post_event()`），`values[key] = current_page`。
- `get()` → current_page；`update(current_page=None, total=None, page_size=None, visible=None)`；属性 `page_count`。
- `current_page` 越界时钳到 `[1, page_count]`。

#### Transfer — 穿梭框
```python
Transfer(source_items, target_items=None, titles=("Source", "Target"),
         size=(18, 8), key=None, enable_events=False, font=None,
         tooltip=None, visible=True, pad=None, expand_x=False, expand_y=False,
         right_click_menu=None, metadata=None)
```
- `tk.Frame` + grid：左列（标题 Label + `tk.Listbox(selectmode="extended")`）、中列 4 个 `ttk.Button`（"›" 选中右移、"»" 全部右移、"‹" 选中左移、"«" 全部左移，`width=2`）、右列同上。
- Listbox 主题：`theme_mod.theme_manager.input_kwargs(include_caret=False)`。
- 标题 Label：muted 色，`anchor="w"`。
- 双击列表项 → 单项移动（左 → 右 / 右 → 左）。
- `get()` → `list(self._target)`；`update(source_items=None, target_items=None, visible=None)` → 整体重设（清空选择）。
- 任何移动后：`enable_events` 时 `_post_event()`（`values[key]` = 目标列表）。
- `apply_theme`：重刷 frame 底色、两个标题色、两个 Listbox 的 `input_kwargs`。

## 5. 导出与 T 前缀

- `elements/__init__.py`：从 `display/panels/selection` 导入 17 个类并加入 `__all__`。
- 包根 `src/TkSimpleGUI/__init__.py`：导入 17 个类 + `T` 前缀别名（`TTag/TBadge/TAvatar/TStatistic/TEmpty/TResult/TSkeleton/TAlert/TWatermark/TCard/TDescriptions/TSteps/TTimeline/TSegmented/TRate/TPagination/TTransfer`），并加入 `__all__`（沿用文件既有分组注释风格）。

## 6. 测试计划（`tests/test_package.py` 追加，约 30 个）

- 每个元素至少：构造 + `window[...]` 取值正确 + 关键 `update()` 生效；canvas 元素断言 `len(widget.find_all())` 合理、`find_all()` 在图元数量变化时不崩。
- 主题跟随：`ts.theme("Slate")` → `apply_theme()`（或 `window.update_theme()`）后 canvas 背景 == `ts.theme_background_color()`；`finally: ts.theme(None)` 复位（既有 TestGauge 的写法）。
- 逻辑型断言：Badge 的 `max_value` 溢出 "99+"、Pagination 的页码窗口/钳位/`ValueError`、Rate 的半星裁剪顶点数、Steps 的状态颜色映射、Tag 的 close 事件、Transfer 的移动、Segmented 的选项变化保值、Skeleton 的 `stop_animation` 不抛、Card 的嵌套 layout 正常 build、Descriptions 的 `get()` dict、Timeline 的 dict/tuple/str 三种输入。
- 3.7 × 3.12 双解释器全绿；`tests/check_syntax.py` 与 `TestPy37Compatibility` 不需修改即通过。

## 7. 验证（五件套 + 目检）

1. `python -m pytest tests -q`
2. `python tests/check_types.py`（ty 零诊断）
3. `D:/bin/ruff.exe check src tests`
4. `python tests/check_syntax.py`
5. `python demos/showcase.py --smoke`
6. 双主题（Daylight / Slate）截图逐控件目检，修到耐看为止。
