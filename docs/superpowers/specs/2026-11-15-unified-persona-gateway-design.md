# 统一人格核心与多 AI 网关设计

## 意图

把第N人格从“Codex Hook + 单一 OpenAI 兼容聊天页”升级为独立的人格规则层。同一份人格可用于 Codex、Claude、Gemini、DeepSeek 和豆包，并由用户明确决定人格是关闭、仅影响当前对话、影响当前 AI，还是影响所有已接入 AI。

## 目标

- 人格只维护一份，可从模板创建、编辑、切换并立即调用。
- Codex 使用 Hook；Claude、Gemini、DeepSeek、豆包使用统一网关和各自协议适配器。
- 提供四种作用域：`off`、`conversation`、`provider`、`global`。
- 切换人格后保留可见聊天和用户事实，但不把旧人格生成的助手回复发送给新人格。
- 页面明确显示“已启用到哪里”，不把“提示已注入”误写成“模型一定遵循”。
- 现有 `/chat` 和 Codex 安装方式保持兼容。

## 非目标

- 不修改任何模型权重、官方客户端内部提示或平台账号设置。
- 不通过浏览器脚本接管 Claude、Gemini、DeepSeek 或豆包官方网页。
- 不承诺提示词能压过平台系统指令、安全策略或模型自身行为。
- 不在本阶段发布 GitHub Tag、Release 或推送 `main`。
- 不在服务端持久保存 API Key。

## 第一性原理与根因

人格影响输出的唯一可靠入口，是在每次模型请求前把当前人格放入该平台支持的高优先级上下文字段。现有实现的问题不是缺少更多平台按钮，而是人格注册、作用域和请求协议都写死在 `server/main.py` 与 `index.html`。

因此根因修复是：

1. 独立人格存储，统一生成可注入上下文。
2. 独立作用域解析，让所有入口使用同一决策。
3. 独立平台适配器，只负责协议转换，不复制人格逻辑。
4. 用人格版本标记助手消息，由网关在服务端执行历史隔离。

## 方案比较

### 方案 A：每个平台单独写插件

平台体验最深，但人格、状态和隔离逻辑会复制五份；Claude、Gemini、DeepSeek、豆包官方客户端也没有统一稳定的本地 Hook。维护成本最高，不采用。

### 方案 B：浏览器扩展注入官方网页

能覆盖部分官方网页，但依赖 DOM、登录态和前端版本，容易失效，也难以证明实际送入模型的内容。不作为核心方案。

### 方案 C：统一人格核心 + 平台适配器 + 可导出提示

人格和作用域保持唯一权威来源；不同平台只转换请求协议。Codex 使用现有 Hook，其他平台通过 API 网关真实注入；无法自动接管的官方客户端提供可复制提示或配置导出。采用此方案。

## 人格模型

内置人格继续从现有目录读取。自定义人格保存到 `server/data/personas/<id>/`，包含：

- `persona.json`：`id`、`name`、`emoji`、`summary`、`description`。
- `SKILL.md`：完整人格契约，也是统一 system prompt 的正文。

创建接口校验：

- `id` 仅允许小写字母、数字和连字符，长度 2–48。
- 不允许覆盖内置人格。
- 名称、简介、规则有明确长度上限。
- 使用模板章节生成 `SKILL.md`，但不伪造“已安装到某平台”。

## 启用与作用域

当前状态增加：

- `enabled: bool`
- `scope: off | conversation | provider | global`
- `provider: codex | claude | gemini | deepseek | doubao | null`
- `conversation_id: string | null`

匹配规则：

- `off`：所有入口返回未注入。
- `conversation`：`provider` 与 `conversation_id` 都匹配才注入。
- `provider`：同一 provider 的所有新请求注入。
- `global`：所有已接入入口注入。

页面内对话生成并持久保存一个本地 `conversation_id`。Codex Hook 从 `UserPromptSubmit` 输入读取 `session_id` 并传给服务，因此可以真正区分 Codex 对话。其他平台 API 调用者需要显式传 `conversation_id`；未传时不能冒充“当前对话”。

## 历史隔离

每条助手历史消息可携带 `persona_version`。网关只转发：

- 所有用户消息。
- 与当前人格版本相同的助手消息。

旧版调用者没有给助手消息标记时，若本轮发生过人格切换，则不转发未标记助手消息；未切换的兼容场景仍按旧行为工作。页面仍显示旧聊天，并插入“已切换至……”系统提示。

## 平台适配器

- `codex`：现有 `UserPromptSubmit` Hook 调用上下文接口，不由 `/chat` 直接调用模型。
- `claude`：Anthropic Messages API，使用顶层 `system`。
- `gemini`：Gemini `generateContent`，使用 `system_instruction` / `systemInstruction` 语义并转换历史角色。
- `deepseek`：OpenAI 兼容 Chat Completions，首条 `system` message。
- `doubao`：火山方舟 OpenAI 兼容 Chat Completions，首条 `system` message，模型字段填写 Endpoint ID。

适配器统一返回回复文本、模型和 provider；上游错误转换为有限长度、无 Key 泄露的本地错误。

## API

- `GET /personas`：动态人格列表。
- `POST /personas`：创建自定义人格。
- `GET /personas/{id}/prompt`：读取统一 prompt。
- `POST /switch`：切换人格并设置启用作用域。
- `POST /enable`：只修改启用状态和作用域，不切人格。
- `GET /context`：按 provider / conversation 查询是否注入。
- `GET /codex/context`：兼容入口，内部使用统一作用域解析。
- `POST /chat`：增加 `provider`、`conversation_id` 和带版本历史，兼容现有 OpenAI 请求字段。

## UI

保持现有深色极简控制台，不重做视觉系统。增加：

- 人格启用开关。
- “当前对话 / 当前 AI / 所有已接入 AI”分段控制。
- 当前 AI 选择：Codex、Claude、Gemini、DeepSeek、豆包。
- 动态人格创建表单。
- API 设置随 provider 显示合理默认地址和说明。
- 状态区显示本地切换、作用域、最近注入证据。

## 安全与兼容

- 服务继续只信任 `127.0.0.1` 和 `localhost`。
- API Key 仅由请求或环境变量提供，不写入项目数据文件。
- 自定义 API Base 必须是完整 HTTP(S) URL，不允许内嵌账号密码。
- 自定义人格文件使用白名单 ID 和固定目录，防止路径穿越。
- 保留现有 `/chat`、`/switch` 请求的默认行为。

## 成功标准

- 同一人格 prompt 能按五个平台的正确协议进入请求。
- `conversation` 作用域不会泄漏到同一 provider 的另一个对话。
- `provider` 作用域不会影响其他 provider。
- 切换后旧助手消息仍可见，但不会进入新请求。
- 可在页面创建人格、切换、启用并立即对话。
- 自动化测试覆盖适配器负载、作用域、路径校验、历史隔离和兼容行为。
- 真实浏览器流程覆盖创建人格、切换作用域、发送对话和状态显示。

