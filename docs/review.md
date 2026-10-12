# TkSimpleGUI 项目审查报告

| 项目 | 内容 |
|---|---|
| 审查基线 | HEAD `0dcfdc1`（`chore: 移除误提交的探针 trace`），工作区干净，47 个 tracked 文件 |
| 审查环境 | Python 3.7.9 / Tk 8.6 / ruff 0.15.4 / ty（`D:\bin\ty.exe`） |
| 审查方式 | 实测优先：先跑测试、类型、语法、lint、冒烟，再对照源码与文档逐项核对 |
| 审查范围 | `src/TkSimpleGUI/`（32 个模块）、`tests/`、`demo.py`、`demos/`、打包与 CI、文档 |

> **重要说明——审查期间仓库被并发修改。**
> 本次审查进行中，有另一个进程在持续提交（HEAD 由 `df0554f` 一路推进到 `0dcfdc1`，包名由
> `PySimpleGUI4` 改为 `TkSimpleGUI`，README 被重写，根目录探针由 92 个清理到 9 个）。
> 本报告已按**最后一次实测**重新核对每一条结论；但阅读时请以当前仓库状态为准。

---

## 一、结论摘要

| 级别 | 项目 | 状态 |
|---|---|---|
| 🔴 P0 | `WINDOW_MIN_WIDTH` NameError —— 库整体不可用，129/181 测试报错 | **审查期间已被并发进程修复**（见 §2.1） |
| 🔴 P0 | `demos/basic_window.py` 引用已删除的 API（`sg.B` / `sg._logger`） | **仍然存在** |
| 🟡 | `tests/check_types.py` 硬编码路径 + 缺失时静默通过 | 仍然存在 |
| 🟡 | `tests/check_syntax.py` 的 "3.7 守卫" 语义不成立 | 仍然存在 |
| 🟡 | 无 ruff 配置；ruff 65 条问题（34 条误报）不入基线 | 仍然存在 |
| 🟡 | `pyproject.toml` 声明了未安装、未声明的 dev 依赖与指标 | 仍然存在 |
| 🟡 | 文档口径冲突：README 称"零第三方依赖"，pyproject 却声明条件依赖 | 仍然存在 |
| 🟡 | README / todo.md 测试数量过期（163 vs 实际 181） | 仍然存在 |
| 🟠 | 根目录残留探针文件未被 `.gitignore` 覆盖 | 仍然存在 |
| 🟠 | 两份 2.2 MB 旧单体 + 过期优化报告 + `_old_tp.py` | 仍然存在 |
| 🟠 | `SelectMode` 重复定义；49 个 T 别名；24 个 popup 函数 | 仍然存在 |
| 🔵 | CI 只发布不测试 | 仍然存在 |

**已验证健康**：单元测试 181 项全通过、ty 零诊断、demo 冒烟通过、3.7 语法解析通过、
`compileall` 干净、无重复定义/裸 except/可变默认参数/TODO 残留。

---

## 二、缺陷

### 2.1 【已修复·记录在案】`WINDOW_MIN_WIDTH` NameError（P0）

**这是本次审查发现的最高危缺陷，已由并发进程在 `3d832dd` 修复。此处记录成因与教训。**

修复前 `src/TkSimpleGUI/window/window.py:487`：

```python
root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
```

而该文件第 12 行是模块导入 `from .. import constants as C`。`WINDOW_MIN_WIDTH` /
`WINDOW_MIN_HEIGHT` 定义在 `constants.py:64-65`，**从未进入 `window.py` 的命名空间**。

调用链与实测报错：

```
File "src\TkSimpleGUI\window\window.py", line 781, in read
    self.finalize()
File "src\TkSimpleGUI\window\window.py", line 417, in finalize
    self._apply_window_options()
File "src\TkSimpleGUI\window\window.py", line 487, in _apply_window_options
    root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
NameError: name 'WINDOW_MIN_WIDTH' is not defined
```

影响面：**每一个 `Window(...).read()` 都会崩**。实测 `python -m unittest discover tests`
为 180 项中 **129 项 ERROR**，`python demo.py --smoke` 直接崩溃。

修复（现已是 `root.minsize(C.WINDOW_MIN_WIDTH, C.WINDOW_MIN_HEIGHT)`）：

```diff
-        root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
+        root.minsize(C.WINDOW_MIN_WIDTH, C.WINDOW_MIN_HEIGHT)
```

**教训（比 bug 本身更重要）**：这条路径**当时没有任何测试覆盖**——测试全绿的时候它就已经是坏的。
"常量搬进 `constants.py`" 这类重构必须配套一次全库引用扫描，并补上覆盖 `finalize()` 的测试。

### 2.2 `demos/basic_window.py` 引用已被删除的 API（P0）

提交 `bafff1d`（`feat!: 删除全部短别名`）移除了短别名，但示例未同步：

| 位置 | 代码 | 实际 |
|---|---|---|
| `demos/basic_window.py:21,23,24` | `sg.B("win_fun")` 等 4 处 | 包只导出 `Button` / `TButton`，**`sg.B` 不存在** → `AttributeError` |
| `demos/basic_window.py:94` | `sg._logger.info("sdfgsdf")` | `_logger` 全库不存在 → `AttributeError` |

`sg.B` 在布局构建阶段即抛错，示例**完全无法运行**。`sg._logger` 那处更隐蔽：它位于事件处理器内，
被 `TkSimpleEvent.apply_event` 的兜底 `except` 吞掉，只在控制台打印一行，不中断程序。

**建议**：修复或删除该示例；给 `demos/` 加 `__init__.py` 或纳入 CI 冒烟。

### 2.3 质量闸门自身的漏洞（🟡，性质比单个 bug 更严重）

| # | 位置 | 问题 |
|---|---|---|
| 1 | `tests/check_types.py:10` | `TY = r"D:\bin\ty.exe"` **硬编码本机绝对路径** |
| 2 | `tests/check_types.py:23-24` | 找不到 ty 时 `print("SKIP...")` 后 **`return 0`** —— 换机器、进 CI、未装 ty 时，这个"零诊断守卫"会**假装通过** |
| 3 | `tests/check_syntax.py:18` | 用 `sys.version` 的 `ast` 解析，却自称 "3.7 compat gate"。**只有恰好用 3.7 运行时该结论才成立**；在 3.12 下它能通过的语法 3.7 未必能过 |
| 4 | 全仓库 | **没有任何 ruff 配置文件**（`ruff.toml` / `.ruff.toml` / `[tool.ruff]` 均无） |
| 5 | `pyproject.toml:50-51,65` | 声明 `timeout` / `timeout_method`（需 pytest-timeout）与 `fail_under = 90`，但 **pytest、pytest-timeout、coverage 实测均未安装**，也没有 `[project.optional-dependencies]` —— 这些指标纯属纸面，从未被测量 |

**ruff 现状**（`ruff check src tests demo.py`，65 条）：
33 `F821` + 1 `F722` + 21 `F401` + 8 `E402` + 2 `E741`。
其中 **34 条是误报**——`cast(Literal["nw","n",...])` 里的字符串被当作前向注解，
因为 ruff 无法解析 `from .._typing_compat import Literal` 那条
`if TYPE_CHECKING / elif / else` 条件导入链。真正需要处理的：

- 21 条 `F401` 未使用导入（20 条可 `--fix` 自动修复）
- 8 条 `E402`：`src/TkSimpleGUI/__init__.py:219-240` 在函数定义之后仍有 import（属有意为之，需 `noqa` 或配置豁免）
- 2 条 `E741`：`src/TkSimpleGUI/elements/chart.py:177,179` 变量名 `l`

ruff **不在 `todo.md` 的回归基线内**，因此这笔债既不可见也不收敛。

### 2.4 运行时健壮性（🟡）

| 位置 | 问题 |
|---|---|
| `src/TkSimpleGUI/event.py:72-73` | `if event not in self._event_handlers` —— 同一事件重复注册被**静默丢弃**，不报错不警告，调试期极难发现 |
| `src/TkSimpleGUI/event.py:114-115` | `apply_event` 吞掉所有 handler 异常只 `print`，配合上一条会掩盖真实故障（见 §2.2 的 `sg._logger`） |

### 2.5 CLI 入口不一致（🟡）

`src/TkSimpleGUI/__init__.py:394` 的文档字符串宣传
`python -m TkSimpleGUI [--version | --themes]`，但 **`src/TkSimpleGUI/__main__.py` 不存在**，
实测 `No module named TkSimpleGUI.__main__`。

`pyproject.toml:33-34` 的 console script（`TkSimpleGUI = "TkSimpleGUI:main"`）是好的，
`main()` 函数也在。**补一个 `__main__.py` 即可**（内容就是 `from . import main; main()`）。

---

## 三、冗余

### 3.1 根目录探针文件（🟠）

```
9 个 _* 文件：___PySimpleGUI4.py  _git_status.py  _grep.py  _led_smoke.txt
              _old_tp.py  _old_view.txt  _r.txt  _tests.txt  _x.txt
```

高峰期曾达 **92 个（约 36,108 行）**，现已被并发进程清理至 9 个，但**问题依旧**：

- `.gitignore:179-187` 只覆盖 `/*.tmp`、`/_split/`、`/_out.txt`、`/_ls*.txt`、`/_st*.txt`，
  **`_*.py` / `_*.txt` 未被忽略**——实测 `git check-ignore _grep.py _b1.txt` 返回 1（未忽略）。
  下一次 `git add -A` 仍会把它们全部提交。
- **建议**：`.gitignore` 增加 `/_*.py`、`/_*.txt`；开发探针统一放 `tests/probes/`（该目录已存在且已成惯例）。

### 3.2 旧单体与过期产物（🟠）

| 文件 | 大小 | 说明 |
|---|---|---|
| `PySimpleGUI4.py` | 2,203,446 B | 旧单文件巨兽，无任何引用 |
| `___PySimpleGUI4.py` | 2,187,407 B | **同一份巨兽的第二份拷贝** |
| `_old_tp.py` | 83,983 B | 旧代码快照 |
| `OPTIMIZATION_REPORT.md` | 8,356 B | 描述已废弃的单文件改造计划（37500 行、移除 `webbrowser`…），与当前架构完全无关 |

合计约 **4.5 MB 死重**。建议删除或移入 `docs/archive/`。

（`logo.png` 已被重写后的 README 第 2 行引用，**不再算死文件**。）

### 3.3 API 面自我重复（🟠）

- `__all__` 共 **233** 个名字、**122** 个类；其中 **49 个 `T` 前缀别名**，
  实测 48 个与原名指向同一个类对象。公共接口凭空翻倍，`__init__.py` 为此多出约 60 行样板。
  （README 已把"两种命名风格"作为卖点，属有意设计——但需权衡 IDE 补全时的噪声。）
- **`SelectMode` 定义了两遍**：`constants.SelectMode` 与 `enums.SelectMode`
  （导出为 `EnumSelectMode`）。实测 `sg.SelectMode is sg.EnumSelectMode` → **False**，
  同一概念两个**不同的枚举类**，互不相等，易踩坑。建议只保留一个。
- **24 个 `popup_*` 函数**高度重叠：`popup_quick` / `popup_quick_message` /
  `popup_auto_close` / `popup_timed` / `popup_annoying` / `popup_notify` /
  `popup_no_titlebar` / `popup_no_buttons` / `popup_non_blocking`。
  建议明确各自语义边界，或合并为带参数的单入口。

---

## 四、缺失

| # | 缺失项 | 说明 |
|---|---|---|
| 1 | **CI 无测试闸门** | `.github/workflows/python-publish.yml` 只在 `v*` tag 上 `uv build` + 发布，**没有任何测试 / 类型 / 语法 / lint 步骤**。当前仓库历史上出现过的"129 个测试报错"状态**可以直接发布到 PyPI** |
| 2 | `src/TkSimpleGUI/__main__.py` | 见 §2.5 |
| 3 | ruff 配置 | 见 §2.3 |
| 4 | dev / optional 依赖声明 | pytest、pytest-timeout、pytest-cov、ruff 均未声明 |
| 5 | 文档目录 | 仅有 README 与 todo.md；无 CHANGELOG、无 CONTRIBUTING、无 API 文档 |
| 6 | `demos/` 缺 `__init__.py` | 且唯一示例是坏的、此前为 untracked |
| 7 | 覆盖窗口构造路径的测试 | 正是 §2.1 逃逸的原因（现应已补上，建议确认） |

---

## 五、文档一致性

### 5.1 README.md

重写后的 README 已基本准确（包名、版本 0.1.0、目录结构、示例代码、TkSimpleGUI 命名均已同步），
仅剩以下问题：

| 位置 | 内容 | 实际 |
|---|---|---|
| `README.md:7`、`README.md:37` | 称"**零第三方依赖**" | `pyproject.toml:24-26` 声明 `typing_extensions; python_version < '3.8'` |
| `README.md:149` | `# unittest 测试套件（163 项）` | **181 项** |
| `README.md:160` | `# 163 项测试` | **181 项** |
| `README.md:115-154` | 目录结构 | 未列出 `input_blocker.py`、`_typing_compat.py`、`py.typed`、`elements/chart.py`、`demos/`、`tests/probes/`、`.github/` |

### 5.2 todo.md

| 位置 | 内容 | 实际 |
|---|---|---|
| `todo.md:5` | 底线"**零第三方依赖**" | 同 §5.1，与 `pyproject.toml` 冲突 |
| `todo.md:109` | "`python -m unittest discover tests`（163 个…）" | **181 个** |

### 5.3 需要拍板的理念冲突

`Literal` 是 Python **3.8** 才进入 `typing` 的。项目用 `_typing_compat.py` 这一层优雅地兼容了 3.7
（条件导入 `typing_extensions`），代码质量没有问题——**问题只在"零第三方依赖"这句口号上**。

两条路，请选一条并统一口径：

- **A. 保留 3.7**：承认 3.7 下存在一个条件依赖，把 README / todo.md 的"零第三方依赖"改为
  "3.8+ 零依赖；3.7 需 `typing_extensions`"。
- **B. 放弃 3.7**：删除 `_typing_compat` 分支与 pyproject 依赖，`requires-python = ">=3.8"`，
  恢复名副其实的零依赖。

---

## 六、已验证通过项

以下均为实测结果，可作为当前健康度基线：

| 检查 | 命令 | 结果 |
|---|---|---|
| 单元测试 | `python -m unittest discover tests` | **181 项，OK**（22 个测试类，覆盖每一个批次） |
| 类型诊断 | `python tests/check_types.py` | **TYPES OK：ty 零诊断** |
| 冒烟自检 | `python demo.py --smoke` | **SMOKE OK** |
| 3.7 语法 | `python tests/check_syntax.py` | **ALL 39 FILES PARSE OK on 3.7.9** |
| 字节编译 | `python -m compileall -q src` | exit 0 |
| 包导入 | `import TkSimpleGUI` | OK，`__version__ = 0.1.0` |
| 静态卫生扫描 | 自建 AST 扫描（32 个模块） | **无重复顶层定义、无裸 `except:`、无可变默认参数、无 TODO/FIXME/XXX/HACK** |

**值得肯定的设计**：
`_typing_compat.py` 的兼容层干净利落；模块职责切分清晰（`elements/` 按控件族分文件、
`window/`、`_theming`、`config`、`enums` 各司其职）；`__slots__` 封装到位；
测试组织规范且按批次可追溯；README 重写后信息密度高、示例可直接运行。

---

## 七、建议处理顺序

1. **修 `demos/basic_window.py`** 的 `sg.B`（4 处）与 `sg._logger`（1 处），或直接删除该示例。
   —— 这是当前唯一仍然"必然报错"的用户可见缺陷。
2. **加固质量闸门**：`check_types.py` 去掉硬编码路径、找不到 ty 时返回**非零**；
   `check_syntax.py` 明确要求以 3.7 解释器运行（或在 CI 中固定 3.7）；
   新增 ruff 配置并把 ruff 纳入回归基线（34 条 `Literal` 误报用 per-file-ignore 处理）。
3. **补 CI**：在 `python-publish.yml` 的构建之前加一个 test job
   （3.7 + 最新版矩阵：`unittest` + `check_types` + `check_syntax` + `demo --smoke` + ruff），
   失败即阻断发布。
4. **清冗余**：删除两份 2.2 MB 旧单体、`_old_tp.py`、`OPTIMIZATION_REPORT.md`；
   `.gitignore` 增加 `/_*.py` 与 `/_*.txt`。
5. **补 `__main__.py`**，让 `python -m TkSimpleGUI` 与文档一致。
6. **统一口径**：README / todo.md 的测试数量改为 181；就 §5.3 的"3.7 vs 零依赖"做出决定。
7. **消歧义**：合并重复的 `SelectMode`；梳理 24 个 `popup_*` 的语义边界。
8. **补 dev 依赖声明**（`[project.optional-dependencies]`），让 `fail_under = 90` 与
   pytest 超时配置真正生效。

---

## 附录：复现命令

```bash
# 基线（全部只读，不改动仓库）
python -m unittest discover tests      # 181 项
python tests/check_types.py            # ty 零诊断守卫
python tests/check_syntax.py           # 逐文件 ast 解析
python demo.py --smoke                 # demo 冒烟
python -m compileall -q src

# lint
python -m ruff check src tests demo.py --statistics

# 示例 API 引用核对（检出 sg.* 中不存在的名字）
python - <<'PY'
import pathlib, re, sys
sys.path.insert(0, "src")
import TkSimpleGUI as sg
names = set()
for p in ["demo.py"] + [str(x) for x in pathlib.Path("demos").rglob("*.py")]:
    names |= set(re.findall(r"\bsg\.([A-Za-z_]\w*)", pathlib.Path(p).read_text(encoding="utf-8")))
print("MISSING:", sorted(n for n in names if not hasattr(sg, n)))
PY

# 冗余排查
git check-ignore -v _grep.py _b1.txt   # exit 1 = 未被忽略
```

---

*报告生成日期：2026-10-12　审查基线：HEAD `0dcfdc1`*
