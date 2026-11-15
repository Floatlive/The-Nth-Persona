# 第N人格 · The Nth Persona

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/Floatlive/The-Nth-Persona?display_name=tag)](https://github.com/Floatlive/The-Nth-Persona/releases)
[![Stars](https://img.shields.io/github/stars/Floatlive/The-Nth-Persona)](https://github.com/Floatlive/The-Nth-Persona)

可切换、可验证、可回滚的本地 AI 人格层。

第N人格把人格规则放进可读的 `SKILL.md`，用本地页面切换当前人格，并通过 Codex `UserPromptSubmit` Hook 把当前规则追加到后续提示中。它不修改模型本身，也不删除聊天记录。

- 当前版本：`v0.3.1`
- 适用范围：个人本地使用、Codex 桌面端接入、OpenAI 兼容 API
- 项目形态：**Skills + Codex Plugin + Local App**

## 使用前提

| 项目 | 要求 |
| --- | --- |
| 操作系统 | Windows、macOS 或 Linux |
| Python | Python 3.10 或更高版本 |
| 首次启动 | 需要联网安装 FastAPI、Uvicorn、HTTPX 和 Pydantic |
| AI 对话 | 用户自行提供 OpenAI 兼容 API 的 Base URL、API Key 和模型名称 |
| Codex 接入 | 运行本地服务，安装并信任项目 Hook |

人格切换、状态查看和规则预览不需要 API Key；只有调用外部模型生成回复时才需要。

## 从 GitHub 下载

1. 打开 [GitHub Releases](https://github.com/Floatlive/The-Nth-Persona/releases)。
2. 下载最新 Release 附件中的 `the-nth-persona-v*.zip`，不要下载来历不明的重新打包文件。
3. 解压到普通可写目录，不要直接在 ZIP 压缩包内运行。
4. 按下方系统说明启动。

## 你能得到什么

- 5 个可切换人格：冷酷执行官、现实毒舌顾问、赛博老中医、极简主义者、信达雅。
- 页面点击切换，立即显示「已切换至【…】」。
- 当前人格只有一个，切换是覆盖，不是叠加。
- Codex 每次提交提示时重新读取当前人格，旧聊天记录继续保留。
- 人格状态原子写入，版本号递增；切换期间的过期回复会被拒绝。
- 本地 API、OpenAI 兼容聊天接口、回归测试和 Windows 安装脚本。

## 3 分钟启动

### Windows

```powershell
.\open.ps1
```

也可以双击 `open.bat`。浏览器打开：

```text
http://127.0.0.1:8000
```

### macOS / Linux

```bash
chmod +x open.sh
./open.sh
```

启动脚本会优先使用项目 `.venv`；依赖缺失时才安装。首次运行后，在页面的 API 设置中填写 OpenAI 兼容服务的 Base URL、API Key 和模型。

默认使用 `127.0.0.1:8000`。如果端口被旧版第N人格或其他服务占用，启动脚本会停止并提示，不会误连；也可以指定其他端口：

```powershell
$env:NTH_PORT = "8010"
.\open.ps1
```

```bash
NTH_PORT=8010 ./open.sh
```

启动器在确认服务可用后，会把当前本机地址写入用户级 `service.json`。Codex Hook 会自动读取该地址，因此使用 `8010` 等自定义端口时不需要再手动修改插件。Windows 配置位于 `%LOCALAPPDATA%\TheNthPersona\service.json`；macOS / Linux 配置位于 `$XDG_CONFIG_HOME/the-nth-persona/service.json` 或 `~/.config/the-nth-persona/service.json`。

## 接入 Codex 桌面端

Windows 上，在项目目录运行：

```powershell
.\install-codex.ps1
```

首次使用时，在 Codex 桌面端审阅并信任 `UserPromptSubmit` Hook，然后保持第N人格服务运行。

> Codex Hook 不是远程控制功能。它只在提交新提示时读取当前人格规则并追加到该轮上下文；不会修改模型本身，也不会删除当前聊天记录。

实际流程：

```text
页面切换人格
    ↓
本地服务保存当前人格和版本
    ↓
Codex 提交新提示
    ↓
Hook 读取 /codex/context
    ↓
当前人格规则追加到本轮模型上下文
```

切换不会新建聊天，也不会清空历史。插件只能影响后续提交的上下文，不能修改模型本身，也不能保证旧聊天内容完全不影响模型。

页面内对话切换人格时，会保留屏幕记录和此前用户消息，但不再把旧助手回复发送给新人格；服务端还会在新人格系统消息中明确要求忽略旧人格语气、结构和立场。Codex 桌面端的旧聊天由 Codex 自身管理，插件无权物理删除，只能在每次新提交时重新注入新人格隔离规则。

页面的「Codex 注入」状态会区分：

1. **本地已切换**：当前人格和版本已写入本地状态。
2. **Hook 已读取**：Codex Hook 最近访问过 `/codex/context`，当前人格规则已由 Hook 输出为附加上下文。
3. **模型实际遵循**：只能从具体回复判断；提示词不是模型权重或硬权限，项目不能保证每次绝对遵循。

第二层是可验证的技术事实，第三层仍受系统指令、开发者指令、聊天历史和模型行为影响。

## 这到底是什么

| 部分 | 类型 | 作用 |
| --- | --- | --- |
| `cold-executor/SKILL.md` 等人格目录 | Agent Skill | 描述每个人格的行为边界和输出规则 |
| `skills/read-current/`、`switcher/` | Agent Skill | 让支持 Skill 的 AI 在对话内读取和切换人格 |
| `codex-plugin/` | Codex Plugin + Hook | 把本地当前人格注入 Codex 后续提示 |
| `server/` + `index.html` | 本地应用 | 提供切换 UI、状态存储和 OpenAI 兼容 API |

因此，第N人格不是一个模型，也不是只能依赖 API 的聊天机器人；它是一个可被不同 AI 工作流读取的规则层。

## 人格列表

| 人格 | ID | 适合 |
| --- | --- | --- |
| 冷酷执行官 | `cold-executor` | 交付结果、最短动作、验收标准 |
| 现实毒舌顾问 | `sharp-advisor` | 用证据检验叙事，指出真实取舍 |
| 赛博老中医 | `cyber-tcm` | 非医疗隐喻与可观察的行为药方 |
| 极简主义者 | `minimalist` | 找出不可省动作，设定停止条件 |
| 信达雅 | `xin-da-ya` | 先信、再达、后雅；完整流程只属于此人格 |

## API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/health` | 服务健康状态 |
| `GET` | `/current` | 当前人格和版本 |
| `POST` | `/switch` | 切换人格，例如 `{"persona":"minimalist"}` |
| `GET` | `/codex/context` | 返回 Codex Hook 使用的当前人格上下文 |
| `GET` | `/integration/status` | 当前人格及本进程最近一次 Codex Hook 读取证据 |
| `GET` | `/personas` | 列出全部人格 |
| `GET` | `/history` | 查看切换历史 |
| `POST` | `/reset` | 重置为默认人格 |
| `POST` | `/chat` | 使用当前人格调用 OpenAI 兼容接口 |

API 文档启动后位于 `http://127.0.0.1:8000/docs`。

## 项目结构

```text
.
├── cold-executor/       # 人格 Skill
├── sharp-advisor/
├── cyber-tcm/
├── minimalist/
├── xin-da-ya/
├── skills/read-current/ # 读取当前人格
├── switcher/            # 对话内切换
├── codex-plugin/        # Codex UserPromptSubmit Hook
├── server/              # FastAPI 服务
├── index.html           # 本地切换与聊天页面
├── tests/               # 回归测试
├── open.ps1 / open.bat / open.sh
└── install-codex.ps1
```

## 开发与验证

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
```

完整开发约定见 [`CONTRIBUTING.md`](CONTRIBUTING.md)，版本变化见 [`CHANGELOG.md`](CHANGELOG.md)。

## 安全与限制

- 项目默认只监听 `127.0.0.1`，不是公网服务。
- API Key 只保存在浏览器 `localStorage` 或本机环境变量；共享设备不要保存。
- 当前是单用户本地版，没有鉴权和多用户隔离。
- Skill 和 Hook 都属于提示层约束，不是模型运行时的硬权限。
- Hook 不读取 API Key，也不读取聊天历史；服务未启动时，本轮不会注入人格。
- 用户级 `service.json` 只保存本机服务地址和更新时间，不保存 API Key 或聊天内容。

## 许可证

MIT © Floatlive
