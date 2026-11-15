# HANDOFF · 第N人格 (The Nth Persona)

> **每次更新后必须刷新本文件。**  
> 转移时：把下面的 **第N人格.zip** 交给另一个 AI，并复制「交接提示词」。

**项目版本：v0.4.0** · **交接文档更新：2026-11-15**

---

## 交接提示词（复制给下一个 AI）

```
这是「第N人格 / The Nth Persona」完整项目包（v0.4.0）。
请先完整阅读 HANDOFF.md，再读 README.md、server/main.py、index.html、各人格 SKILL.md。开始修改前先核对实际文件，不要仅凭本交接文档推断代码现状。

硬性规则：
1. 不要重复已完成工作；先对照 HANDOFF「已完成 / 未做」
2. 信达雅完整「先信→再达→后雅」只属于 xin-da-ya，禁止复制到其他人设
3. 同一时间只允许一个人格生效；页面切换写 server/data/current.json；已启用 Codex Hook 时，后续提示读取当前人格
4. 每轮改动结束：更新 HANDOFF.md 版本与清单，并重新打包 第N人格.zip

项目形态：
- 可点击切换的人格库 + FastAPI（/switch /current /chat）
- 页面点击立即 Toast「已切换至【…】」，并可在页内用 OpenAI 兼容 API 对话（Key 存在浏览器 localStorage）
- 也可不启动服务：把 CHAT_BOOTSTRAP.md 贴进任意 AI 对话使用

当前目标：以“本地内置脚本服务 + UI 调用”为主，统一支持 Codex、Claude、Gemini、DeepSeek 和豆包；不部署公网。GitHub 已完成 `v0.3.0` 首次版本发布，`v0.4.0` 代码尚未创建 Tag 或 Release。
```

**转移文件**：`第N人格.zip`（与本 HANDOFF 同级的压缩包，内含完整目录）

GitHub：https://github.com/Floatlive/The-Nth-Persona  
仓库为 Public，默认分支为 `main`。首次初始化提交 `56421dc` 已推送；`v0.3.0` 为首个版本标签和 GitHub Release。不要索要或让用户在聊天中粘贴 Personal Access Token。

---

## 1. 项目是什么

面向「和 AI 对话」的可切换高优先级人格系统：

| 层 | 作用 |
|----|------|
| 人格 Skill | 每人一个 `SKILL.md`，独立行为协议 + 安全边界 + 输出判据 |
| 前端 `index.html` | 点卡片切换；Toast「已切换至」；页内聊天 |
| 后端 `server/main.py` | 状态唯一文件 + `/chat` 注入当前人格 system prompt |
| `CHAT_BOOTSTRAP.md` | 无服务时，复制到任意 AI 即可切换 |
| `open.sh` | 缺依赖则 pip 安装 → 启动 uvicorn → 开浏览器 |

双路径（不要拆掉）：
1. **页面路径**：点选 → `POST /switch` → `/chat` 用当前人格调 LLM  
2. **纯对话路径**：用户说「切换到毒舌」→ switcher / read-current 规则，不依赖本机 API

---

## 2. 已完成 / 未做

### 已完成
- [x] 命名：第N人格 / The Nth Persona
- [x] 5 人格 Skill（独立行为协议、历史边界、禁止事项、示例）
- [x] 信达雅完整三难流程（仅 xin-da-ya）；其他人设仅轻量信/达/雅底线
- [x] 前端点击切换 + Toast + 对话区系统消息「已切换至【…】」
- [x] FastAPI：`/health` `/version` `/current` `/switch` `/history` `/personas` `/personas/{id}/prompt` `/reset` `/chat`；`GET /` 托管页面
- [x] `/chat`：读当前人格 SKILL 为 system，转发 OpenAI 兼容接口
- [x] 前端 API 设置（Base / Key / Model → localStorage）
- [x] `read-current` / `switcher` 改为**对话优先**，API 可选
- [x] `CHAT_BOOTSTRAP.md`、`persona-template`、`open.sh`（自动装依赖）
- [x] MIT、.gitignore、README、HANDOFF 制度、references/SOURCES.md
- [x] 本机联调：switch / current / prompt / 无 Key 时 chat 400 均已验证
- [x] v0.2.6：重制响应式本地 UI（桌面侧栏、人格卡片、对话工作区、状态面板、API 设置）
- [x] UI 保留五个人格独立描述；完整「先信→再达→后雅」只在 xin-da-ya 卡片中体现
- [x] UI 支持服务连接状态提示；服务在线时切换写入 current.json，离线打开时明确提示仅预览
- [x] 更新前端 / FastAPI / README 版本号至 0.2.6
- [x] v0.2.7：移除宽松 CORS；current/history 原子写入并加进程内锁；损坏状态文件安全回退；前端改为后端确认后切换，切换/聊天互斥；聊天携带人格版本并校验，避免旧人格响应混入新会话；移除打包缓存文件
- [x] v0.2.9：增加本地 Host 白名单；Windows / macOS / Linux 启动入口统一优先使用项目 `.venv`，缺依赖时才安装；增加后端回归测试入口
- [x] v0.3.0：增加 Codex `UserPromptSubmit` 插件 Hook 与 `/codex/context`，切换后 Codex 后续提示读取当前人格
- [x] v0.3.1：分别增强五个人格的独立决策协议和安全边界；新增人格契约回归测试
- [x] v0.4.0：动态人格创建；四档启用作用域；Codex / Claude / Gemini / DeepSeek / 豆包统一适配；服务端旧人格历史隔离

### 未做 / 可继续
- [ ] 多用户（`user_id` 仍 default；无鉴权）
- [x] 定位为个人本地客户端使用，不计划公网部署
- [x] 增加 Windows 启动入口 `open.bat` 与 `open.ps1`；保留 `open.sh`（需在目标 Windows 机器实测）
- [x] 更新 `.gitignore`，排除本地人格状态、历史、密钥文件、日志、虚拟环境和缓存；ZIP 不包含运行时状态 JSON
- [x] 新建人格表单 / 更多人格
- [ ] 人格输出自动评测（fixture）
- [x] GitHub 首次初始化提交（`56421dc`，已推送至 `main`）
- [x] `v0.3.0` Git 标签与 GitHub Release
- [ ] 流式输出（SSE）聊天

---

## 3. v0.2.7 修复记录（历史）

- 本地服务仅由启动脚本绑定 `127.0.0.1`，不开放通配 CORS。
- `current.json` 与 `history.json` 使用临时文件 + `os.replace` 原子替换；状态读写在单进程内加锁。
- 前端先等待 `/switch` 成功再更新当前人格；切换期间禁用切换与发送，离线模式明确标注为预览。
- `/chat` 固定读取本轮人格快照，并校验前端传入的 `persona_version`；状态已变化时返回 409。
- `user_id` 暂时仍是兼容字段，项目依旧为单用户本地版，不提供鉴权或真正多用户隔离。
- CORS 已移除；直接双击 HTML 仅支持离线预览，需通过 `open.sh` 启动后端才能持久化切换与聊天。


## 3A. v0.2.9 修复记录

- FastAPI 增加 `TrustedHostMiddleware`，只接受 `127.0.0.1` 与 `localhost`，拒绝伪造 Host 头。
- `open.ps1` 与 `open.sh` 使用项目 `.venv`；服务已运行时不重复安装，依赖缺失时才安装，不再每次升级 pip。
- 新增 `tests/` 与 `requirements-dev.txt`，当前回归测试覆盖 Host 白名单、损坏版本恢复和重置版本递增。

## 3B. v0.2.8 修复记录

- `/reset` 读取旧状态并递增版本号；重置动作写入历史，版本号不会倒退。
- 当前状态版本必须是正整数（排除 bool）；发现损坏版本时，参考历史版本恢复并原子写回。
- JSON 读取同时处理无效 UTF-8；聊天请求限制历史最多 20 条，并限制消息、API Key、API Base、模型字段长度。
- `/chat` 在上游模型响应后再次检查当前人格与版本，期间发生切换则返回 409，拒绝旧人格回复。
- 前端只在 `file://` 模式启用离线预览切换；通过本地 HTTP 服务访问时，网络异常会保留原状态。
- 发送期间禁用清空对话，清空函数也增加发送状态保护。
- 已完成 Python/JavaScript 语法、状态版本递增、损坏数据恢复、重置递增、前端状态分支、请求输入限制和 ZIP 完整性测试；真实模型 API 端到端测试仍需有效 API Key。

## 3C. v0.2.8 打包与启动补充（历史）

- ZIP 文件名统一使用 `第N人格-v0.2.8.zip`，版本标识保持 `v0.2.8`，不在正式版本名中加入“修复版”等临时描述。
- 已修正 ZIP 中文文件名的 UTF-8 编码标记。
- ZIP 内包含 `open.bat`、`open.ps1`、`open.sh` 三种启动入口。
- `.gitignore` 已忽略 `server/data/current.json`、`server/data/history.json`、`.env`、日志、虚拟环境及缓存。
- 当前 ZIP 实际有 22 个条目（含目录项），包含项目源码、人格 Skill、说明文档和启动脚本；`server/data/` 保留为空目录，运行时的 `current.json` 与 `history.json` 不打包。
- UI 文件 `index.html` 与此前单独交付的 `第N人格-UI-v0.2.8.html` 内容一致。

## 3D. v0.2.9 打包与启动补充

- 正式 ZIP 文件名为 `第N人格-v0.2.9.zip`。
- ZIP 实际包含 25 个条目，保留项目源码、人格 Skill、启动脚本、`requirements-dev.txt` 与回归测试；不包含 `.venv`、运行时日志、缓存或状态 JSON。
- `server/data/` 保留为空目录，运行时状态不会随包分发。

## 3E. v0.3.0 Codex 接入

- Codex 插件位于 `codex-plugin/`，本机插件市场定义位于 `.agents/plugins/marketplace.json`。
- Windows 安装入口为 `install-codex.ps1`；首次启用后，用户需在 Codex 桌面端审阅并信任 Hook。
- `UserPromptSubmit` 每轮请求 `http://127.0.0.1:8000/codex/context`，直接读取当前人格 `SKILL.md`；不读取 API Key 或聊天历史。
- 必须启动第N人格本地服务；服务未运行时本轮不会注入人格，并显示提示。
- Hook 只影响提交后的模型上下文，不修改模型，也不能删除同一聊天中的旧消息或保证旧内容绝对不影响模型。
- 验证：pytest 7 项通过；当前 Codex CLI 在临时 `CODEX_HOME` 中成功添加本地市场并安装插件；安装缓存中的 Hook 在 Windows PowerShell 5.1 下通过人格注入、UTF-8、无 Key 和服务离线提示测试。
- 尚未完成：Codex 桌面端首次信任 Hook，以及在真实桌面聊天中观察一次模型回复。不得把隔离 CLI / Hook 测试表述成桌面端回复验收完成。

## 3F. v0.3.1 人格规则增强与浏览器检查

- 五个人格分别采用独立决策协议；修正提示词错误宣称可覆盖其他指令的问题。
- 历史使用要求限定为当前可见且相关的内容；读取其他聊天须由用户明确提及并允许。
- 真实浏览器已验证五个人格切换、切换提示、刷新后当前人格持久化、无 API Key 时的明确错误提示，以及清空聊天不改变当前人格。
- 浏览器出现非阻断的 `/favicon.ico` 404 和密码输入框未放入表单提示。
- 由于未配置用户 API Key，真实模型成功回复流程未执行；不得称端到端模型调用已验收。
- 回归测试：`11 passed`。

## 3E. 测试边界与待验证项

已知检查记录包括 Python/JavaScript 语法、ZIP 完整性、前端 DOM ID 引用、后端状态版本与损坏恢复逻辑、请求长度限制等。此前报告的隔离环境后端测试结果不能替代用户设备上的完整验收。以下仍未确认：

- [ ] Windows 实机双击 `open.bat` 启动及浏览器打开
- [ ] Windows PowerShell 执行 `open.ps1`
- [x] 在真实浏览器中点击五个人格、刷新验证状态持久化、检查缺失 API Key 的聊天错误与清空流程
- [ ] 使用用户自己的有效 API Key 完成真实模型 API 端到端聊天
- [ ] 使用用户自己的有效 API Key 完成真实模型 API 端到端聊天
- [ ] macOS/Linux 启动脚本在目标设备上的实测

不要将“语法检查通过”表述成“UI 已在真实浏览器完整测试通过”。

## 4. 目录结构

```
第N人格/
├── HANDOFF.md              ← 本文件
├── CHAT_BOOTSTRAP.md       ← 复制到任意 AI
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── .gitignore
├── SKILL.md                ← 包入口 Skill
├── open.sh
├── open.ps1
├── open.bat
├── index.html
├── install-codex.ps1        ← 添加并安装本机 Codex 插件
├── .agents/plugins/marketplace.json
├── codex-plugin/            ← Codex UserPromptSubmit Hook
├── references/SOURCES.md
├── server/
│   ├── main.py
│   ├── requirements.txt    ← fastapi uvicorn httpx pydantic
│   └── data/
│       ├── current.json    ← 当前人格（页面路径真相）
│       └── history.json
├── cold-executor/SKILL.md
├── sharp-advisor/SKILL.md
├── cyber-tcm/SKILL.md
├── minimalist/SKILL.md
├── xin-da-ya/SKILL.md
├── switcher/SKILL.md
├── skills/read-current/SKILL.md
├── persona-template/SKILL.md
├── requirements-dev.txt     ← pytest
└── tests/
    ├── test_host_validation.py
    └── test_state.py
```

---

## 5. 人格表

| ID | 中文名 | 要点 |
|----|--------|------|
| cold-executor | 冷酷执行官 | 交付结果 / 最短动作 / 验收标准 |
| sharp-advisor | 现实毒舌顾问 | 证据检验叙事 / 指出真实取舍 / 不辱骂 |
| cyber-tcm | 赛博老中医 | 状态隐喻 / 行为实验 / 非医疗建议 |
| minimalist | 极简主义者 | 唯一目标 / 不可省动作 / 停止条件 |
| xin-da-ya | 信达雅 | 完整 信→达→雅（独家） |

---

## 6. 怎么跑

```bash
cd 第N人格
chmod +x open.sh    # 若权限未保留
./open.sh           # 或 bash open.sh
# 浏览器 http://127.0.0.1:8000
```

手动：

```bash
cd 第N人格/server
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

页内「API 设置」填 OpenAI 兼容 Base + Key + 模型后发送消息。  
不启服务时：把 `CHAT_BOOTSTRAP.md` 全文贴进对话。

---

## 7. API 速查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 前端页面 |
| GET | `/health` | 健康检查 |
| GET | `/current` | 当前人格 |
| POST | `/switch` | body: `{"persona":"sharp-advisor"}` → `已切换至【…】` |
| GET | `/personas/{id}/prompt` | 该人格 system 文本 |
| POST | `/chat` | body: message + history + 可选 api_key/api_base/model/persona_version |
| GET | `/history` | 切换历史 |
| POST | `/reset` | 回到冷酷执行官 |

环境变量（可选，代替页面填 Key）：`NTH_API_KEY` / `OPENAI_API_KEY`、`NTH_API_BASE`、`NTH_MODEL`。

---

## 8. UI 说明

- `index.html` 为响应式深色桌面工作台，窄屏自动改为单列布局。
- 页面包含人格库、当前人格状态、对话工作区、服务状态和 OpenAI 兼容 API 设置。
- API Key 仍只存浏览器 `localStorage`；共享设备不要保存，远程 API 使用 HTTPS。
- 推荐使用 `bash open.sh` 启动后端后访问 `http://127.0.0.1:8000`，以获得人格切换持久化和页内 AI 对话。
- 直接双击 `index.html` 可离线预览界面；此时无法调用本地 API，切换仅为页面预览，不会写入 `server/data/current.json`。

## 9. 关键决策（勿轻易推翻）

- 主场景是**和 AI 对话**，不是重定制垂直 Agent
- 必须支持**点击切换**并立刻可见「已切换至」
- 信达雅完整流程不共享；轻量质量底线可共享
- 人格之间禁止互相调用 / 混输出结构
- 每轮交付必须带更新后的 HANDOFF + zip

---

## 10. 已知限制（诚实）

- 人格 Skill 是模型上下文中的提示约束，不是运行时权限；不能覆盖系统、开发者指令或安全边界，模型仍可能漂移
- `/chat` 依赖用户自备 API Key；项目不内置模型
- 单用户、无鉴权，仅面向个人本机使用；不要直接暴露到公网
- `open.sh` 在部分环境 chmod 位可能不保留 → 用 `bash open.sh`
- GitHub 首次发布需确认远程仓库与本地提交状态；本项目不在文档中记录访问令牌

---

## 11. 维护约定

1. 改完 → 更新本文件版本、已完成、日期 → 打 zip  
2. 新人格：优先通过 UI 或 `POST /personas` 创建；内置人格仍使用仓库目录
3. 禁止把 xin-da-ya 三段式完整流程贴进其他人设  

**正式项目包文件名**：当前未生成 `v0.4.0` Release ZIP；不要把工作树临时文件当作发布包。
