# 第N人格 · The Nth Persona

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](./README.md)

可切换的高优先级 AI 人格系统（Skill 包 + 前端页面 + API）。

Click to switch personas. One active persona at a time. Built for Claude Code / Cursor-style agent skills.

---

## Features

- **5 built-in personas** with high-priority enforcement rules
- **Click-to-switch UI** + FastAPI backend (same-origin; no wildcard CORS)
- **`read-current` skill** so the AI always loads the latest persona
- **Persona template** for adding the N+1th persona
- **Handoff doc** for transferring the project to another AI
- Atomic local state writes, monotonic persona versions, corruption recovery, and request concurrency checks
- Local-only Host header protection and project-level virtual-environment startup
- Windows Codex plugin hook reads the selected persona for each new prompt

## Personas

| Persona | ID | Style |
|---------|-----|--------|
| 冷酷执行官 | `cold-executor` | Results & deadlines only |
| 现实毒舌顾问 | `sharp-advisor` | Sharp, rational call-outs |
| 赛博老中医 | `cyber-tcm` | TCM metaphors + actionable “prescriptions” |
| 极简主义者 | `minimalist` | Cut everything non-essential |
| 信达雅 | `xin-da-ya` | Faithfulness → Clarity → Elegance |

> Full 信→达→雅 process belongs **only** to `xin-da-ya`. Other personas share a light quality baseline only.

## UI 本地使用

推荐下载完整 ZIP 并解压，在项目目录运行：

Windows：双击 `open.bat`，或在 PowerShell 中运行 `.\open.ps1`。

macOS / Linux：运行 `bash open.sh`。

浏览器打开 `http://127.0.0.1:8000`。首次运行会自动安装后端依赖。启动后可持久化人格切换，并在页面内配置 OpenAI 兼容 API 进行对话。

也可以直接双击 `index.html` 预览 UI；离线预览不具备后端切换持久化和 AI 对话能力。项目按个人本地使用设计，不需要公网服务器。API Key 保存在当前浏览器 localStorage；共享设备请勿保存 Key，远程 API 地址请使用 HTTPS。

## Codex 桌面端

Windows 上运行 `.\install-codex.ps1` 注册并安装本地 Codex 插件。首次使用时，在 Codex 桌面端审阅并信任 `UserPromptSubmit` Hook；然后启动第N人格应用。之后每次提交提示，Hook 会从本机 `/codex/context` 读取当前人格规则并追加到 Codex 的模型上下文。

切换只影响后续提交，不清空或重开当前聊天。历史助手发言仍留在上下文里，因此插件会明确要求 Codex 不沿用旧人格，但不能保证旧内容绝对不影响模型。若第N人格服务未启动，该轮会提示未注入人格。

## Quick Start

Windows：双击 `open.bat`。

macOS / Linux：
```bash
chmod +x open.sh
./open.sh
```

Or:

```bash
cd server
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

Open **http://127.0.0.1:8000**

- Page: `/`
- API docs: `/docs`
- Health: `/health`

## Run Tests

启动一次后，项目 `.venv` 已创建。安装测试工具并运行回归测试：

Windows：
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
```

macOS / Linux：
```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest
```

## Install as Agent Skill

Copy this repository (or the skill folders) into your agent skills directory:

- Claude Code → `.claude/skills/`
- Cursor → corresponding skills / agents path

Then say: `打开第N人格` or `切换到冷酷执行官`.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | UI |
| GET | `/health` | Health check |
| GET | `/current` | Active persona |
| POST | `/switch` | Switch `{"persona":"cold-executor"}` |
| GET | `/history` | Switch history |
| GET | `/personas` | List personas |
| POST | `/reset` | Reset to default |
| POST | `/chat` | Chat with the active persona through an OpenAI-compatible API |

## Project Layout

```
.
├── HANDOFF.md                 # Transfer notes for another AI
├── requirements-dev.txt       # Test dependencies
├── open.sh                    # macOS / Linux 一键启动
├── open.ps1                   # Windows PowerShell 一键启动
├── open.bat                   # Windows 双击启动
├── index.html                 # Switch UI
├── server/                    # FastAPI (UI + API)
├── cold-executor/             # Persona skills
├── sharp-advisor/
├── cyber-tcm/
├── minimalist/
├── xin-da-ya/
├── skills/read-current/       # Force-read active persona
├── switcher/
├── persona-template/          # Template for new personas
└── tests/                     # Backend regression tests
```

## Design Rules

1. Only one persona active at a time (full replace, not stack)
2. `server/data/current.json` is the single source of truth (with `version`)
3. AI must read latest state via `read-current` before replying
4. Extensible: copy `persona-template` to add persona N+1

## License

MIT © Floatlive


## v0.3.0 · Codex 接入

- 增加 Codex `UserPromptSubmit` 插件 Hook，每轮从 `/codex/context` 读取最新人格规则。
- Hook 不读取 API Key 或聊天历史；服务不可用时提示本轮未注入。
- 当前人格仅影响后续提交，不会清除旧聊天上下文。

## v0.2.9 修复

- 增加 `TrustedHostMiddleware`，仅接受 `127.0.0.1` 与 `localhost`，拒绝伪造 Host 头。
- Windows / macOS / Linux 启动入口统一优先使用项目 `.venv`；只有服务未运行且依赖缺失时才安装依赖。
- 增加后端回归测试入口，覆盖本地 Host 白名单。

## v0.2.8 修复

- 重置人格时版本号继续递增，避免旧版本号被重新使用。
- 修复无效版本字段和非 UTF-8 状态文件的恢复处理。
- 模型返回前再次核对人格版本，切换期间产生的旧人格回复将以 409 拒绝。
- HTTP 服务请求失败时不再误判为离线预览；仅直接打开 HTML（`file://`）时允许离线预览切换。
- 发送期间禁用清空对话，并在清空函数中增加保护。
- 限制聊天历史条数及相关输入字段长度。
