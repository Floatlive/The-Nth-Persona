# 人格注入可验证性设计

## 意图

让自定义端口下的 Codex Hook 仍能读取当前人格，并把“本地已切换”“Hook 已读取”“模型已遵循”三个层级明确分开。用户应能验证人格确实进入了对话上下文，同时不会被误导为模型权重或 AI 本身已被修改。

## 目标

- 启动器将当前服务地址写入用户级运行配置，插件缓存目录中的 Hook 可独立读取。
- Hook 地址优先级为 `NTH_PERSONA_CODEX_URL`、用户级运行配置、默认 `8000`。
- 服务记录本进程最近一次 `/codex/context` 读取的时间、人格和版本。
- 页面能显示 Codex Hook 尚未读取或最近读取的事实状态。
- 集成测试证明 `/chat` 的首条上游消息是当前人格 `system` prompt，Hook 输出包含当前人格规则。

## 非目标

- 不修改模型权重、Codex 系统提示或桌面端内部实现。
- 不保证模型每次绝对遵循人格。
- 不删除或隐藏旧聊天记录。
- 不创建新的聊天上下文、Tag 或 GitHub Release。

## 约束

- 保持单用户、本地服务、默认仅监听 `127.0.0.1`。
- Hook 运行位置可能是 Codex 插件缓存目录，不能依赖仓库相对路径。
- API Key 不进入 Hook 或运行配置。
- 状态只证明服务端点被读取，不把“读取”表述成“模型已遵循”。

## 方案比较

### 方案 A：要求用户手动设置环境变量

改动最少，但每次自定义端口都需要额外配置，且桌面端继承环境变量不稳定。不能解决默认体验的断链。

### 方案 B：启动器写用户级运行配置，Hook 每轮读取

启动器是实际服务地址的权威来源；用户级配置不依赖插件安装目录。实现简单，可跨项目目录和插件更新保留。选用此方案。

### 方案 C：让 Hook 扫描本机端口

无需配置文件，但慢、不可预测，也可能连到错误服务，违背现有服务身份校验原则，不采用。

## 设计

`server/runtime_config.py` 负责把服务地址原子写入用户级 `service.json`。Windows 使用 `%LOCALAPPDATA%\TheNthPersona\service.json`，其他系统使用 `$XDG_CONFIG_HOME/the-nth-persona/service.json`，未设置时回退 `~/.config/the-nth-persona/service.json`。配置只包含服务基础地址、Codex 上下文地址和更新时间。

`open.ps1` 与 `open.sh` 仅在确认正确版本服务可用后写配置。PowerShell Hook 先读取显式环境变量；未设置时读取 Windows 用户级配置；配置缺失或损坏时回退 `http://127.0.0.1:8000/codex/context`。

服务在每次成功进入 `/codex/context` 时记录 UTC 时间、当前人格和版本。`GET /integration/status` 返回当前人格状态和最近一次 Codex 读取证据。页面用极简文字显示“Hook 尚未读取”或最近读取时间；该状态不宣称模型已遵循。

`/chat` 测试使用本地 ASGI 假上游捕获真实 HTTP 请求，断言第一条消息的角色为 `system` 且包含当前人格名称与规则。Hook 测试运行真实 PowerShell 脚本和真实本地服务，断言输出的 `additionalContext` 包含当前人格。

## 成功标准

- `NTH_PORT=8010` 启动后，不设置额外 Hook 环境变量也能读取 `8010`。
- 页面切换人格后，`/chat` 与 Hook 都注入同一人格版本。
- `/integration/status` 能区分“本地已切换”和“Hook 最近读取”。
- 文档明确：人格影响的是后续模型上下文，不是 AI 模型本身。
