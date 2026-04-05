# QuantKit Implementation Plan

终端版个人投资工具包，面向同时交易 A 股和美股的个人投资者。学习和反思工具，不是自动交易系统。

## Milestones

- [x] Phase 1: Infrastructure & Data Layer (Tasks 1-4)
- [x] Phase 2: Portfolio & Analysis Engines (Tasks 5-8)
- [x] Phase 3: CLI & Integration (Tasks 9-10)
- [x] Phase 4: Documentation (Task 11)
- [x] Phase 5: UX Improvements (IBKR CSV, submenu loops, prompts)

## Tasks

| Task | Status | Tests | Implementer |
|------|--------|-------|-------------|
| 1. Project Scaffold | ✅ | - | Codex CLI |
| 2. Settings & Config | ✅ | 3 | Codex CLI |
| 3. SQLite Cache Layer | ✅ | 4 | Codex CLI |
| 4. Data Provider | ✅ | 4 | Codex CLI |
| 5. Portfolio Management | ✅ | 5 | Codex CLI |
| 6. Factor Check Engine | ✅ | 12 | Codex CLI |
| 7. Backtest Engine | ✅ | 4 | Codex CLI |
| 8. Risk Lens Engine | ✅ | 4 | Codex CLI |
| 9. CLI Menu System | ✅ | - | Codex CLI |
| 10. Integration Test | ✅ | 1 | Codex CLI |
| 11. Documentation | ✅ | - | Claude Code |
| UX Fix: Submenu loops + IBKR CSV + prompts | ✅ | +2 | Codex CLI |

**Total: 37 tests, all passing.**

## Team

- **Claude Code**: Architect & PM — design, plan, review, test, commit, documentation
- **Codex CLI**: Developer — all code implementation
- **Gemini CLI**: QA & Documentation — attempted doc generation (tool limitations)
