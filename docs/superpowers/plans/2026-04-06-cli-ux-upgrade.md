# CLI UX Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Rich Prompt with prompt_toolkit for auto-completion, fish-style symbol suggestions, and unified visual style.

**Architecture:** New `prompt.py` handles all prompt_toolkit integration (completer, auto-suggest, session, styles). `cli.py` main loop switches from `Prompt.ask()` to `PromptSession.prompt()`. Command handlers get visual unification (ROUNDED tables, Rule headers). No changes to routing or business logic.

**Tech Stack:** prompt-toolkit>=3.0, rich (existing)

---

### Task 1: Add prompt-toolkit dependency

**Files:**
- Modify: `pyproject.toml:10`

- [ ] **Step 1: Add prompt-toolkit to dependencies**

In `pyproject.toml`, add `"prompt-toolkit>=3.0"` to the `dependencies` list. The dependencies section should become:

```toml
dependencies = [
    "rich>=13.0",
    "plotext>=5.2",
    "pandas>=2.0",
    "numpy>=1.24",
    "yfinance>=0.2.31",
    "tushare>=1.4",
    "pyyaml>=6.0",
    "prompt-toolkit>=3.0",
]
```

- [ ] **Step 2: Install and verify**

Run: `uv pip install -e ".[dev]"`
Expected: Successfully installs prompt-toolkit

Run: `uv run python -c "from prompt_toolkit import PromptSession; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "feat: add prompt-toolkit dependency for CLI auto-completion"
```

---

### Task 2: SymbolAutoSuggest

**Files:**
- Create: `src/quantkit/prompt.py`
- Create: `tests/test_prompt.py`

- [ ] **Step 1: Write failing tests for SymbolAutoSuggest**

Create `tests/test_prompt.py`:

```python
"""Tests for prompt_toolkit integration layer."""

from prompt_toolkit.document import Document

from quantkit.prompt import SymbolAutoSuggest


class TestSymbolAutoSuggest:
    def test_no_suggestion_when_empty(self):
        suggest = SymbolAutoSuggest()
        doc = Document("AA")
        result = suggest.get_suggestion(None, doc)
        assert result is None

    def test_suggests_matching_symbol(self):
        suggest = SymbolAutoSuggest()
        suggest.add("AAPL")
        doc = Document("AA")
        result = suggest.get_suggestion(None, doc)
        assert result is not None
        assert result.text == "PL"

    def test_no_suggestion_when_no_prefix_match(self):
        suggest = SymbolAutoSuggest()
        suggest.add("AAPL")
        doc = Document("GO")
        result = suggest.get_suggestion(None, doc)
        assert result is None

    def test_dedup_most_recent_first(self):
        suggest = SymbolAutoSuggest()
        suggest.add("AAPL")
        suggest.add("AMZN")
        suggest.add("AAPL")
        assert suggest.symbols == ["AAPL", "AMZN"]

    def test_no_suggestion_for_slash_input(self):
        suggest = SymbolAutoSuggest()
        suggest.add("AAPL")
        doc = Document("/f")
        result = suggest.get_suggestion(None, doc)
        assert result is None

    def test_case_insensitive_match(self):
        suggest = SymbolAutoSuggest()
        suggest.add("AAPL")
        doc = Document("aa")
        result = suggest.get_suggestion(None, doc)
        assert result is not None
        assert result.text == "PL"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_prompt.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'quantkit.prompt'`

- [ ] **Step 3: Implement SymbolAutoSuggest**

Create `src/quantkit/prompt.py`:

```python
"""prompt_toolkit integration: completer, auto-suggest, session, styles."""

from __future__ import annotations

from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion
from prompt_toolkit.document import Document


class SymbolAutoSuggest(AutoSuggest):
    """Fish-style auto-suggest from successfully loaded stock symbols."""

    def __init__(self) -> None:
        self.symbols: list[str] = []

    def add(self, symbol: str) -> None:
        """Add a symbol to the suggestion list. Most recent first, no duplicates."""
        upper = symbol.upper()
        if upper in self.symbols:
            self.symbols.remove(upper)
        self.symbols.insert(0, upper)

    def get_suggestion(self, _buffer: object, document: Document) -> Suggestion | None:
        """Return suggestion if text prefix-matches a known symbol."""
        text = document.text.strip()
        if not text or text.startswith("/"):
            return None
        upper_text = text.upper()
        for sym in self.symbols:
            if sym.startswith(upper_text) and len(sym) > len(upper_text):
                return Suggestion(sym[len(upper_text):])
        return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_prompt.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/quantkit/prompt.py tests/test_prompt.py
git commit -m "feat: add SymbolAutoSuggest for fish-style stock code suggestions"
```

---

### Task 3: QuantKitCompleter

**Files:**
- Modify: `src/quantkit/prompt.py`
- Modify: `tests/test_prompt.py`

- [ ] **Step 1: Write failing tests for QuantKitCompleter**

Append to `tests/test_prompt.py`:

```python
from unittest.mock import patch

from prompt_toolkit.completion import CompleteEvent

from quantkit.prompt import QuantKitCompleter


def _get_completions(completer, text, cursor_pos=None):
    """Helper: get completion list from a completer for given text."""
    if cursor_pos is None:
        cursor_pos = len(text)
    doc = Document(text, cursor_pos)
    event = CompleteEvent()
    return list(completer.get_completions(doc, event))


class TestQuantKitCompleter:
    def test_slash_shows_commands(self):
        completer = QuantKitCompleter()
        completions = _get_completions(completer, "/")
        texts = [c.text for c in completions]
        assert "factor" in texts
        assert "backtest" in texts
        assert "exit" in texts

    def test_slash_partial_filters(self):
        completer = QuantKitCompleter()
        completions = _get_completions(completer, "/fa")
        texts = [c.text for c in completions]
        assert "ctor" in texts
        assert len(texts) == 1

    def test_guru_hidden_when_persona_off(self):
        with patch("quantkit.prompt.load_config", return_value={"persona_mode": False}):
            completer = QuantKitCompleter()
            completions = _get_completions(completer, "/")
            texts = [c.text for c in completions]
            assert "guru" not in texts

    def test_guru_shown_when_persona_on(self):
        with patch("quantkit.prompt.load_config", return_value={"persona_mode": True}):
            completer = QuantKitCompleter()
            completions = _get_completions(completer, "/")
            texts = [c.text for c in completions]
            assert "guru" in texts

    def test_backtest_param_completion(self):
        completer = QuantKitCompleter()
        completions = _get_completions(completer, "/backtest ")
        texts = [c.text for c in completions]
        assert "ma" in texts
        assert "dca" in texts

    def test_guru_param_completion(self):
        from quantkit.persona.engine import Persona, Rule

        persona = Persona(
            name="Test",
            name_en="testguru",
            philosophy="test",
            rules=[Rule(factor="pe", op="<", threshold=20, weight=1, hit="g", miss="b")],
            buy_threshold=0.7,
            watch_threshold=0.4,
        )
        with patch("quantkit.prompt.load_config", return_value={"persona_mode": True}):
            with patch("quantkit.prompt.load_personas", return_value=[persona]):
                completer = QuantKitCompleter()
                completions = _get_completions(completer, "/guru ")
                texts = [c.text for c in completions]
                assert "testguru" in texts
                assert "all" in texts

    def test_no_completion_for_plain_text(self):
        completer = QuantKitCompleter()
        completions = _get_completions(completer, "AAPL")
        assert completions == []

    def test_no_completion_for_empty(self):
        completer = QuantKitCompleter()
        completions = _get_completions(completer, "")
        assert completions == []

    def test_completions_have_display_meta(self):
        completer = QuantKitCompleter()
        completions = _get_completions(completer, "/fac")
        assert len(completions) == 1
        assert completions[0].display_meta is not None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_prompt.py::TestQuantKitCompleter -v`
Expected: FAIL — `ImportError: cannot import name 'QuantKitCompleter'`

- [ ] **Step 3: Implement QuantKitCompleter**

Add to `src/quantkit/prompt.py` (after the existing `SymbolAutoSuggest` class):

```python
from prompt_toolkit.completion import CompleteEvent, Completion, Completer

from quantkit.commands import COMMANDS
from quantkit.config import load_config
from quantkit.persona.engine import load_personas

STRATEGIES = {"ma": "MA Cross (5/20)", "dca": "DCA (Monthly)"}


class QuantKitCompleter(Completer):
    """Three-layer completer: commands, parameters, nothing for plain text."""

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> list[Completion]:
        text = document.text_before_cursor.lstrip()

        if not text.startswith("/"):
            return

        parts = text.split(None, 1)
        cmd_part = parts[0]  # e.g. "/backtest" or "/fa"

        if len(parts) == 1 and not text.endswith(" "):
            # Still typing command name — complete commands
            prefix = cmd_part[1:]  # strip leading "/"
            cfg = load_config()
            persona_on = cfg.get("persona_mode", False)

            for name, info in COMMANDS.items():
                if info.requires_persona and not persona_on:
                    continue
                if name.startswith(prefix):
                    yield Completion(
                        name[len(prefix):],
                        display=f"/{name}",
                        display_meta=info.description,
                    )
            return

        # Command is complete — try parameter completion
        cmd_name = cmd_part[1:].lower()
        arg_text = parts[1].strip() if len(parts) > 1 else ""

        if cmd_name == "backtest":
            for key, desc in STRATEGIES.items():
                if key.startswith(arg_text.lower()):
                    yield Completion(
                        key[len(arg_text):],
                        display=key,
                        display_meta=desc,
                    )
        elif cmd_name == "guru":
            cfg = load_config()
            if cfg.get("persona_mode", False):
                candidates = {"all": "全部投资人"}
                for p in load_personas():
                    candidates[p.name_en] = p.name
                for key, desc in candidates.items():
                    if key.startswith(arg_text.lower()):
                        yield Completion(
                            key[len(arg_text):],
                            display=key,
                            display_meta=desc,
                        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_prompt.py -v`
Expected: 15 passed

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: 71+ passed (no regressions)

- [ ] **Step 6: Commit**

```bash
git add src/quantkit/prompt.py tests/test_prompt.py
git commit -m "feat: add QuantKitCompleter with command and parameter auto-completion"
```

---

### Task 4: PromptSession creation and prompt styling

**Files:**
- Modify: `src/quantkit/prompt.py`
- Modify: `tests/test_prompt.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_prompt.py`:

```python
from quantkit.prompt import create_session, get_prompt_message


class TestGetPromptMessage:
    def test_no_context(self):
        result = get_prompt_message(ctx=None, persona_mode=False)
        # FormattedText is a list of (style, text) tuples
        text = "".join(t for _, t in result)
        assert "❯" in text
        assert "AAPL" not in text

    def test_with_context(self):
        from unittest.mock import MagicMock

        ctx = MagicMock()
        ctx.symbol = "AAPL"
        result = get_prompt_message(ctx=ctx, persona_mode=False)
        text = "".join(t for _, t in result)
        assert "AAPL" in text
        assert "❯" in text
        assert "🎭" not in text

    def test_with_persona_mode(self):
        from unittest.mock import MagicMock

        ctx = MagicMock()
        ctx.symbol = "AAPL"
        result = get_prompt_message(ctx=ctx, persona_mode=True)
        text = "".join(t for _, t in result)
        assert "AAPL" in text
        assert "🎭" in text
        assert "❯" in text


class TestCreateSession:
    def test_returns_prompt_session(self):
        from prompt_toolkit import PromptSession

        suggest = SymbolAutoSuggest()
        session = create_session(suggest)
        assert isinstance(session, PromptSession)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_prompt.py::TestGetPromptMessage -v`
Expected: FAIL — `ImportError: cannot import name 'get_prompt_message'`

- [ ] **Step 3: Implement create_session and get_prompt_message**

Add to `src/quantkit/prompt.py` (after `QuantKitCompleter`):

```python
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style as PtStyle


PROMPT_STYLE = PtStyle.from_dict({
    "completion-menu.completion": "bg:#333333 #ffffff",
    "completion-menu.completion.current": "bg:#00aa00 #ffffff bold",
    "completion-menu.meta.completion": "bg:#333333 #aaaaaa",
    "completion-menu.meta.completion.current": "bg:#00aa00 #aaaaaa",
    "auto-suggest": "#666666",
    "symbol": "bold ansibrightcyan",
    "chevron": "ansigreen",
    "persona-icon": "",
})


def get_prompt_message(
    ctx: object | None, persona_mode: bool
) -> FormattedText:
    """Build the prompt as FormattedText. ctx must have .symbol attribute if not None."""
    parts: list[tuple[str, str]] = []
    if ctx is not None:
        parts.append(("class:symbol", ctx.symbol))  # type: ignore[union-attr]
        parts.append(("", " "))
        if persona_mode:
            parts.append(("class:persona-icon", "🎭 "))
    parts.append(("class:chevron", "❯ "))
    return FormattedText(parts)


def create_session(symbol_suggest: SymbolAutoSuggest) -> PromptSession:
    """Create a configured PromptSession with completer, auto-suggest, and styles."""
    return PromptSession(
        completer=QuantKitCompleter(),
        auto_suggest=symbol_suggest,
        style=PROMPT_STYLE,
        complete_while_typing=True,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_prompt.py -v`
Expected: 19 passed

- [ ] **Step 5: Commit**

```bash
git add src/quantkit/prompt.py tests/test_prompt.py
git commit -m "feat: add PromptSession creation and formatted prompt styling"
```

---

### Task 5: Rewrite cli.py main loop

**Files:**
- Modify: `src/quantkit/cli.py`

- [ ] **Step 1: Rewrite cli.py**

Replace the entire content of `src/quantkit/cli.py` with:

```python
"""Stock-centric command-driven CLI for QuantKit."""

from __future__ import annotations

import os
import sys

from rich import box
from rich.console import Console
from rich.panel import Panel

from quantkit.commands import route
from quantkit.config import load_config
from quantkit.prompt import SymbolAutoSuggest, create_session, get_prompt_message
from quantkit.stock_context import StockContext

console = Console()

VERSION = "0.1.0"


def _show_banner() -> None:
    """Display startup banner."""
    console.print(
        Panel(
            f"[bold green]QuantKit[/bold green] v{VERSION}\n"
            "Personal Investment Toolkit\n\n"
            "输入股票代码开始 · /help 查看命令",
            box=box.ROUNDED,
            border_style="green",
            padding=(1, 2),
        )
    )


def main() -> None:
    """Main loop: stock-centric command interface with auto-completion."""
    if sys.stdout.isatty():
        os.system("clear")  # noqa: S605

    _show_banner()

    symbol_suggest = SymbolAutoSuggest()
    session = create_session(symbol_suggest)
    ctx: StockContext | None = None

    while True:
        try:
            cfg = load_config()
            persona_mode = cfg.get("persona_mode", False)
            prompt_msg = get_prompt_message(ctx, persona_mode)
            user_input = session.prompt(prompt_msg).strip()

            if not user_input:
                continue

            if user_input.startswith("/"):
                result = route(user_input, ctx)
                if result == "exit":
                    console.print("[dim]Goodbye.[/dim]")
                    break
            else:
                symbol = user_input.upper()
                console.print(f"[bold]Fetching data for {symbol}...[/bold]")
                try:
                    new_ctx = StockContext.load(symbol)
                    ctx = new_ctx
                    symbol_suggest.add(symbol)
                    info_parts = [f"1y OHLCV ({len(ctx.ohlcv)} bars)"]
                    if ctx.has_fundamentals:
                        info_parts.append("fundamentals")
                    else:
                        info_parts.append("[yellow]fundamentals unavailable[/yellow]")
                    console.print(f"[green]Done[/green] ({', '.join(info_parts)})")
                except ValueError as exc:
                    console.print(Panel(str(exc), title="Error", border_style="red"))
                except Exception as exc:
                    console.print(Panel(str(exc), title="Error", border_style="red"))

        except KeyboardInterrupt:
            console.print()
            continue
        except EOFError:
            console.print("\n[dim]Goodbye.[/dim]")
            break
```

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All tests pass. The integration tests mock at the `route`/`parse_command` level which is unchanged.

- [ ] **Step 3: Commit**

```bash
git add src/quantkit/cli.py
git commit -m "feat: rewrite CLI main loop with prompt_toolkit PromptSession"
```

---

### Task 6: Visual unification — analysis.py

**Files:**
- Modify: `src/quantkit/commands/analysis.py`

- [ ] **Step 1: Update analysis.py with ROUNDED tables and Rule headers**

Make these changes to `src/quantkit/commands/analysis.py`:

1. Add import at top (after existing imports):
```python
from rich import box
from rich.rule import Rule
```

2. In `cmd_factor()`, replace line 46:
```python
    table = Table(title=f"{ctx.symbol} Factor Check", show_lines=True)
```
with:
```python
    console.print(Rule(f"Factor Check: {ctx.symbol}", style="cyan"))
    table = Table(show_lines=True, box=box.ROUNDED, title_style="bold cyan")
```

3. In `cmd_backtest()`, replace line 126:
```python
    table = Table(title="Performance Metrics", show_lines=True)
```
with:
```python
    console.print(Rule(f"Backtest: {ctx.symbol} — {strategy_name}", style="cyan"))
    table = Table(show_lines=True, box=box.ROUNDED, title_style="bold cyan")
```

4. In `cmd_risk()`, replace line 200:
```python
    table = Table(show_lines=True)
```
with:
```python
    table = Table(show_lines=True, box=box.ROUNDED)
```

5. In `cmd_risk()`, replace line 214:
```python
        corr_table = Table(show_lines=True)
```
with:
```python
        corr_table = Table(show_lines=True, box=box.ROUNDED)
```

6. In `cmd_risk()`, replace line 239 (vol_table):
```python
        vol_table = Table(show_lines=True)
```
with:
```python
        vol_table = Table(show_lines=True, box=box.ROUNDED)
```

7. Replace the 4 section headers in `cmd_risk()`:
```python
    console.print("\n[bold underline]1. Concentration[/bold underline]")
```
→
```python
    console.print(Rule("1. Concentration", style="cyan"))
```

```python
        console.print("\n[bold underline]2. Correlation Matrix[/bold underline]")
```
→
```python
        console.print(Rule("2. Correlation Matrix", style="cyan"))
```

```python
        console.print("\n[bold underline]3. Volatility Contribution[/bold underline]")
```
→
```python
        console.print(Rule("3. Volatility Contribution", style="cyan"))
```

```python
    console.print("\n[bold underline]4. Historical Drawdown[/bold underline]")
```
→
```python
    console.print(Rule("4. Historical Drawdown", style="cyan"))
```

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All pass (output formatting changes don't break functional tests)

- [ ] **Step 3: Commit**

```bash
git add src/quantkit/commands/analysis.py
git commit -m "feat: unify analysis output with ROUNDED tables and Rule headers"
```

---

### Task 7: Visual unification — persona_cmd.py

**Files:**
- Modify: `src/quantkit/commands/persona_cmd.py`

- [ ] **Step 1: Update persona_cmd.py**

Make these changes to `src/quantkit/commands/persona_cmd.py`:

1. Add imports:
```python
from rich import box
from rich.rule import Rule
```

2. In `_display_verdict()`, change the Panel to use ROUNDED box. Replace line 38-45:
```python
    console.print(
        Panel(
            content,
            title=f"{persona_name}视角: {symbol}",
            border_style="cyan",
            padding=(1, 2),
        )
    )
```
with:
```python
    console.print(
        Panel(
            content,
            title=f"{persona_name}视角: {symbol}",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )
```

3. In `cmd_guru()`, add a Rule header before evaluation. After line 60 (`factors = ctx.get_factors()`), add:
```python
    console.print(Rule(f"Guru: {ctx.symbol}", style="cyan"))
```

4. In `cmd_guru()`, change the summary table (line 86):
```python
        summary = Table(title=f"{ctx.symbol} — 投资人总览", show_lines=True)
```
to:
```python
        summary = Table(
            title=f"{ctx.symbol} — 投资人总览",
            show_lines=True,
            box=box.ROUNDED,
            title_style="bold cyan",
        )
```

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All pass

- [ ] **Step 3: Commit**

```bash
git add src/quantkit/commands/persona_cmd.py
git commit -m "feat: unify persona output with ROUNDED box and Rule headers"
```

---

### Task 8: Visual unification — management.py

**Files:**
- Modify: `src/quantkit/commands/management.py`

- [ ] **Step 1: Update management.py**

Make these changes to `src/quantkit/commands/management.py`:

1. Add imports:
```python
from rich import box
from rich.rule import Rule
```

2. In `cmd_portfolio()`, replace line 26:
```python
        console.print(Panel("Portfolio Management", style="bold cyan"))
```
with:
```python
        console.print(Rule("Portfolio", style="cyan"))
```

3. In `cmd_portfolio()`, change the positions table (line 52):
```python
                table = Table(title="Positions", show_lines=True)
```
to:
```python
                table = Table(
                    title="Positions", show_lines=True, box=box.ROUNDED, title_style="bold cyan"
                )
```

4. In `cmd_settings()`, replace line 81:
```python
        table = Table(show_lines=True)
```
with:
```python
        table = Table(show_lines=True, box=box.ROUNDED)
```

5. In `cmd_settings()`, replace line 91:
```python
        console.print(Panel("Settings", style="bold cyan"))
```
with:
```python
        console.print(Rule("Settings", style="cyan"))
```

6. In `cmd_help()`, change the help table (line 137):
```python
    table = Table(title="Available Commands", show_lines=True)
```
to:
```python
    console.print(Rule("Help", style="cyan"))
    table = Table(show_lines=True, box=box.ROUNDED)
```

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All pass

- [ ] **Step 3: Commit**

```bash
git add src/quantkit/commands/management.py
git commit -m "feat: unify management output with ROUNDED tables and Rule headers"
```

---

### Task 9: Update integration tests

**Files:**
- Modify: `tests/test_integration.py`

- [ ] **Step 1: Verify existing integration tests still pass**

Run: `uv run pytest tests/test_integration.py -v`
Expected: All pass (integration tests test `parse_command`/`route`/`StockContext`, not `Prompt.ask`)

If they pass, no changes needed. If any test imports or mocks `rich.prompt.Prompt` for the main loop, update the mock target.

- [ ] **Step 2: Run the full test suite one final time**

Run: `uv run pytest tests/ -v`
Expected: 71+ tests pass, 0 failures

- [ ] **Step 3: Run ruff lint**

Run: `uv run ruff check src/ tests/`
Expected: No errors

- [ ] **Step 4: Commit if any changes were needed**

```bash
git add tests/
git commit -m "test: update integration tests for prompt_toolkit CLI"
```

(Skip this step if no changes were needed.)

---

### Task 10: Documentation updates

**Files:**
- Modify: `PROJECT.md`
- Modify: `GUIDE.md`
- Modify: `LOG.md`

- [ ] **Step 1: Update PROJECT.md**

Add `prompt-toolkit>=3.0` to the Dependencies section in `pyproject.toml` description area if referenced.

In the Directory Structure section, add under `src/quantkit/`:
```
│   ├── prompt.py            # prompt_toolkit 集成（补全/建议/样式）
```

- [ ] **Step 2: Update GUIDE.md**

In the "基本操作" section, add a note about auto-completion:

```markdown
**自动补全**：输入 `/` 自动弹出命令菜单，Tab 或方向键选择。`/backtest ` 和 `/guru ` 后会补全参数。输入股票代码时，之前查过的代码会以灰色提示。
```

- [ ] **Step 3: Update LOG.md**

Add entry under `## 2026-04-06`:

```markdown
### CLI UX Upgrade: prompt_toolkit + 视觉统一

- **Who**: Codex CLI（由 Claude Code 调度）
- **What**:
  - 主循环输入层从 Rich Prompt 换为 prompt_toolkit PromptSession
  - 输入 `/` 自动弹命令补全菜单，参数补全（策略/投资人）
  - fish-style 灰色建议历史股票代码
  - 启动清屏 + 品牌 banner
  - 所有表格统一 ROUNDED 圆角 + Rule 标题头
  - 补全菜单深色主题
- **设计文档**: `docs/superpowers/specs/2026-04-06-cli-ux-upgrade-design.md`
- **新增依赖**: prompt-toolkit>=3.0
```

- [ ] **Step 4: Commit**

```bash
git add PROJECT.md GUIDE.md LOG.md
git commit -m "docs: update documentation for CLI UX upgrade"
```
