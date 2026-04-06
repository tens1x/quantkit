# CLI UX Upgrade Design Spec

## Goal

用 prompt_toolkit 替换 Rich Prompt 作为主循环输入层，实现自动补全、历史建议、统一视觉风格。启动时清屏。

## Architecture

prompt_toolkit 管输入，Rich 管输出。新增 `prompt.py` 作为集成层，不修改命令路由和业务逻辑。

## Dependencies

- 新增 `prompt-toolkit>=3.0` 到 `pyproject.toml`

---

## 1. 启动体验

### 清屏

启动时清屏，仅在交互终端下执行：

```python
if sys.stdout.isatty():
    os.system("clear")
```

### Banner

```
╭──────────────────────────────────────╮
│  QuantKit v0.1.0                     │
│  Personal Investment Toolkit         │
│                                      │
│  输入股票代码开始 · /help 查看命令    │
╰──────────────────────────────────────╯
```

Rich Panel，rounded box，green 边框。

### Prompt 样式

用 prompt_toolkit formatted text（不用 Rich markup）：

- 未选股票：`❯ `（绿色 ❯）
- 选了股票：`AAPL ❯ `（bold cyan 股票码 + 绿色 ❯）
- persona_mode 开启：`AAPL 🎭 ❯ `

函数签名：`get_prompt_message(ctx, persona_mode) → FormattedText`

---

## 2. 自动补全

### 总体策略

一个 `QuantKitCompleter(Completer)` 子类，按输入状态组合分发，不做继承树。

### 第一层：命令补全

输入 `/` 自动弹下拉菜单。候选项从 `COMMANDS` 注册表动态生成，每次补全时读取：

```
/factor      因子分析
/backtest    策略回测
/risk        持仓风险分析
/portfolio   持仓管理
/settings    设置
/help        显示可用命令
/exit        退出
```

- `/guru` 仅在 `load_config()` 返回 `persona_mode=True` 时出现
- 每次触发补全时动态读 config，不缓存（保证 `/settings` 切换后立即生效）

### 第二层：参数补全

命令后空格触发。按命令名分派：

| 命令 | 候选来源 |
|------|---------|
| `/backtest` | 共享常量 `STRATEGIES = {"ma": "MA Cross", "dca": "DCA Monthly"}` |
| `/guru` | `load_personas()` 动态取 `name_en` 列表 + `all` |
| 其他命令 | 无参数补全 |

### 第三层：历史股票建议

非 `/` 开头的输入，用自定义 `SymbolAutoSuggest(AutoSuggest)` 提供 fish-style 灰色建议。

**关键决策**：不使用 `AutoSuggestFromHistory`（会混入命令、路径、日期等噪音）。维护独立的成功加载 symbol 集合：

```python
class SymbolAutoSuggest(AutoSuggest):
    def __init__(self):
        self.symbols: list[str] = []  # 按时间倒序

    def add(self, symbol: str):
        # 去重，最新在前
        ...

    def get_suggestion(self, buffer, document):
        # 前缀匹配 symbols 列表
        ...
```

- 只有 `StockContext.load()` 成功后才 `add(symbol)`
- 会话级，不持久化

---

## 3. 视觉风格统一

### 配色方案

| 用途 | 颜色 |
|------|------|
| 品牌/成功 | green |
| 次要标题/边框 | cyan |
| 因子红绿灯 | green/yellow/red（保持现有） |
| 弱化提示 | dim |
| 错误 | red |

### 表格风格

所有 Rich Table 统一：
- `box=box.ROUNDED`（圆角边框）
- 标题 bold cyan
- 数值列右对齐（已有）

涉及文件：`analysis.py`、`persona_cmd.py`、`management.py`

### 命令输出头部

每个命令输出前用 `Rich.Rule` 替代各自不同的标题方式：

```python
console.print(Rule(f"Factor Check: {ctx.symbol}", style="cyan"))
```

替换现有的 Table title / Panel title 混用。

### 补全菜单样式

prompt_toolkit 的 `Style` 定义：

```python
style = Style.from_dict({
    "completion-menu.completion":          "bg:#333333 #ffffff",
    "completion-menu.completion.current":  "bg:#00aa00 #ffffff bold",
    "completion-menu.meta.completion":     "bg:#333333 #aaaaaa",
    "completion-menu.meta.completion.current": "bg:#00aa00 #aaaaaa",
    "auto-suggest":                        "#666666",
})
```

---

## 4. 架构

### 新增文件

**`src/quantkit/prompt.py`** — prompt_toolkit 集成层，4 个组件：

| 组件 | 职责 |
|------|------|
| `QuantKitCompleter` | 三层补全分发（命令/参数/无） |
| `SymbolAutoSuggest` | 独立的 symbol 历史建议 |
| `create_session(symbol_suggest)` | 创建配置好的 `PromptSession`（含 patch_stdout、样式、completer） |
| `get_prompt_message(ctx, persona_mode)` | 返回 `FormattedText` 格式的 prompt |

### 修改文件

| 文件 | 改动 |
|------|------|
| `cli.py` | 主循环换 `PromptSession.prompt()`，启动清屏，维护 symbol_suggest |
| `commands/analysis.py` | 表格 `ROUNDED` box，输出头 `Rule` |
| `commands/persona_cmd.py` | 同上 |
| `commands/management.py` | 同上（子菜单内部仍用 `rich.prompt.Prompt`） |
| `pyproject.toml` | 新增 `prompt-toolkit>=3.0` |

### 不变的文件

- `commands/__init__.py` — `COMMANDS`、`route()`、`parse_command()` 全部不动
- `stock_context.py`、`persona/engine.py`、`factor/`、`backtest/`、`risk/` — 不动

### prompt_toolkit + Rich 混用注意事项

1. **patch_stdout**：`create_session()` 使用 `patch_stdout=True`，确保命令执行期间的 `console.print()` 和 `plotext.show()` 不干扰输入行
2. **prompt text**：用 prompt_toolkit 自己的 `FormattedText`，不用 Rich markup
3. **子菜单**：仍用 `rich.prompt.Prompt`，串行调用不冲突（过渡方案）

---

## 5. 数据流

```
用户键入 → PromptSession.prompt()
                │
                ├── 输入 "/" → QuantKitCompleter
                │                ├── 读 COMMANDS + load_config() → 命令候选
                │                └── 读 STRATEGIES / load_personas() → 参数候选
                │
                └── 其他输入 → SymbolAutoSuggest → 灰色建议

用户回车 → cli.py 主循环
                │
                ├── "/" 开头 → route() → handler → Rich 输出
                │
                └── 其他 → StockContext.load()
                           ├── 成功 → symbol_suggest.add(symbol)
                           └── 失败 → 错误 Panel
```

---

## 6. 测试计划

### 新增测试

| 测试文件 | 覆盖内容 |
|---------|---------|
| `tests/test_prompt.py` | QuantKitCompleter 单测：命令补全、参数补全、guru 过滤、空输入 |
| `tests/test_prompt.py` | SymbolAutoSuggest 单测：add/去重/前缀匹配 |

### 现有测试

- `test_commands.py`、`test_cli_routing.py` — 不受影响（测 parse_command/route，不测输入层）
- `test_integration.py` — 可能需要调整 mock（如果 mock 了 Prompt.ask）

### 不测的

- 补全菜单视觉渲染（需要终端，CI 不稳定）
- 清屏行为（isatty 判断，trivial）

---

## 7. 边界情况

- **窄终端**：ROUNDED box + CJK 字符需要手动测试宽度
- **非 TTY**：清屏跳过，prompt_toolkit 自动降级为 dumb 模式
- **Ctrl-C**：prompt_toolkit 原生支持，抛 `KeyboardInterrupt`，主循环 catch 后 continue
- **Ctrl-D**：prompt_toolkit 抛 `EOFError`，主循环 catch 后 break
- **persona_mode 切换**：补全每次动态读 config，立即生效
- **无 persona YAML**：`/guru` 补全返回空列表，不报错
