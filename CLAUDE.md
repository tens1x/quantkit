# QuantKit — Agent 协作规范

所有参与本项目的 AI agent 必须遵守以下约定。这是铁律，不是建议。

## 项目简介

终端版个人投资学习工具。Python 3.11+，Rich TUI，SQLite 缓存。不是自动交易系统。

## 分工

| 角色 | Agent | 做什么 | 不做什么 |
|------|-------|--------|---------|
| Architect & PM | Claude Code | 设计、拆任务、review、跑测试、commit、写文档 | 写实现代码 |
| Developer | Codex CLI | 写实现代码、写测试代码 | 做设计决策、自行 commit |
| QA & Docs | Gemini CLI | 辅助分析、second review | 写实现代码 |

**违规示例：** Claude Code 直接写 `engine.py` 的实现 → 违规。应该交给 Codex。
**例外：** 紧急 hotfix（测试全挂、项目跑不起来）时 Claude Code 可以直接修，但必须在 LOG.md 记录原因。

## Git 规范

### Commit Message

```
<type>: <description>

Co-Authored-By: <agent> <email>
```

Type:
- `feat:` 新功能
- `fix:` 修 bug
- `docs:` 文档
- `test:` 测试
- `refactor:` 重构（不改行为）

Co-Author:
- Codex: `Co-Authored-By: Codex CLI <noreply@openai.com>`
- Claude: `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`
- Gemini: `Co-Authored-By: Gemini CLI <noreply@google.com>`

### 提交前必须

1. `uv run pytest tests/ -v` 全部通过
2. 不提交 `.env`、`*.db`、`.venv/`、`.runtime/`
3. 一个 commit 做一件事，不混杂

### 分支

当前阶段直接在 `main` 上开发。将来功能复杂后再引入 feature branch。

## 代码规范

### Python 风格

- 类型注解：公开函数必须有参数和返回值类型注解
- Docstring：公开函数必须有一行描述
- 命名：函数 `snake_case`，类 `PascalCase`，常量 `UPPER_SNAKE`
- 私有函数前缀 `_`
- 文件头部 docstring 说明模块职责
- 不用 `# type: ignore` 除非有明确原因

### 文件组织

- 每个文件一个明确职责
- 新模块遵循现有目录结构（`src/quantkit/<module>/`）
- 测试文件 `tests/test_<module>.py`，一对一对应

### 依赖

- 新增依赖必须加到 `pyproject.toml` 的 `dependencies`
- 开发依赖加到 `[project.optional-dependencies] dev`
- 不引入重型框架，保持轻量

## 测试规范

### 要求

- 每个公开函数至少一个测试
- 新策略：至少测信号生成 + 回测运行
- 新因子：至少测评级逻辑的 green/yellow/red 三档
- 用 `tmp_path` 和 `monkeypatch` 隔离，不依赖真实文件系统或网络
- Mock 外部 API（yfinance、tushare），不在测试中发真实请求

### 命名

```python
def test_<功能>_<场景>():
    # e.g. test_rate_factor_pe_green
    # e.g. test_import_ibkr_csv
```

### TDD 流程

1. 先写测试，跑一遍确认失败
2. 写最小实现让测试通过
3. 重构（如果需要）
4. 全量测试通过 → commit

## 文档规范

### 改了代码必须同步更新的文档

| 改了什么 | 更新什么 |
|---------|---------|
| 新增/修改模块接口 | PROJECT.md 的 Module Interfaces |
| 新增策略 | PROJECT.md + GUIDE.md + PLAN.md backlog |
| 新增因子 | PROJECT.md + GUIDE.md |
| Bug fix / UX 改进 | LOG.md |
| 架构变更 | PROJECT.md + LOG.md |

### LOG.md 记录规则

每次有意义的变更都要记录：
- **Who**: 谁做的
- **What**: 做了什么
- **Why**: 为什么这么做（最重要）
- **Commit**: hash

## CLI 规范

- Stock-centric 命令驱动：用户输入股票代码 → `/命令` 交互
- 所有用户交互通过 `rich.prompt.Prompt`
- 错误显示用红色 Panel，不暴露 traceback
- 命令 handler 在 `commands/` 模块中，通过 `route()` 分发
- 中英混合提示：技术名词英文，操作引导中文
- 数据获取前显示 "Fetching data for XXX..."

## 添加新功能的标准流程

```
1. research/strategies/ 写策略文档（或 research/papers/ 写论文笔记）
2. Claude Code 出设计方案，确认接口
3. Codex 实现代码 + 测试
4. Claude Code review：
   - 测试全过？
   - 接口符合 PROJECT.md？
   - CLI 交互符合规范？
5. Commit + push
6. 更新 PROJECT.md、GUIDE.md、LOG.md、PLAN.md
```

## 运行命令速查

```bash
uv run python -m quantkit          # 运行
uv run pytest tests/ -v            # 全量测试
uv run pytest tests/test_xxx.py -v # 单模块测试
git log --oneline -10              # 最近提交
```
