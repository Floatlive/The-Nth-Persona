# 第N人格功能清单

本清单以仓库 `v0.4.2` 实现为基线，用于说明当前能力、验证证据和已知边界。`[x]` 表示有对应自动化测试或已完成的人工验收；具体证据见每一项。

## 本轮验收记录（2026-11-15）

- 完整自动化回归：`python -m pytest -q -p no:cacheprovider`，71 passed。
- 真实浏览器验收：1440×900 桌面和 390×844 手机视口均无横向溢出；已操作人格切换、聊天历史保留、当前页面/当前 AI 作用域、Codex 单聊天禁用、API 设置和自定义人格创建/切换。
- 对话闭环使用仅监听本机的模拟 OpenAI 兼容接口，验证切换后用户历史进入请求、旧人格助手回复被过滤、新人格规则作为 system 消息发送；未调用真实模型、未验证真实服务商 API 凭据。
- 浏览器控制台无 error。手机验收截图：`output/playwright/final-regression/mobile.png`。

## 启动与本地服务

- [x] Windows 可通过 `open.ps1` 或 `open.bat` 启动；macOS / Linux 可通过 `open.sh` 启动。测试：`tests/test_startup_scripts.py`。
- [x] 通过 `NTH_PORT` 指定本机端口；Hook 从用户级 `service.json` 读取服务地址和令牌。测试：`tests/test_runtime_config.py`、`tests/test_codex_hook.py`。
- [x] 启动时检查已有服务的项目身份和版本，避免误连其他服务。测试：`tests/test_service_probe.py`。
- [x] 服务默认仅监听回环地址，并校验 Host。测试：`tests/test_host_validation.py`。
- [x] 提供 `/health`、`/version` 和 `/docs` 接口。

## 人格管理

- [x] 内置冷酷执行官、现实毒舌顾问、赛博老中医、极简主义者、信达雅五种人格；人格规则位于各自 `SKILL.md`。
- [x] UI 可切换人格、自定义人格、查看当前人格、查看切换历史和重置。实现：`index.html`、`server/persona_store.py`、`server/main.py`。测试：`tests/test_persona_store.py`、`tests/test_state.py`。
- [x] 自定义人格使用统一模板，验证 ID、字段长度和人格文件路径。测试：`tests/test_persona_store.py`。
- [x] 当前状态和历史记录使用原子写入及版本号；异常状态安全恢复。测试：`tests/test_state.py`、`tests/test_activation.py`。

## 生效范围

- [x] 支持关闭、当前页面、当前 AI、所有接入四种范围；当前页面使用 `sessionStorage` 生成的页面 ID。测试：`tests/test_activation.py`、`tests/test_ui_contract.py`。
- [x] Codex 仅支持“当前 AI”和“所有接入”；Codex 单聊绑定已移除，因为服务无法可靠识别 UI 当前选中的聊天。测试：`tests/test_activation.py`、`tests/test_codex_integration.py`、`tests/test_ui_contract.py`。
- [x] Codex Hook 按提交读取当前人格；它不会清除或重写 Codex 聊天记录。测试：`tests/test_codex_hook.py`、`tests/test_codex_integration.py`。
- [x] 本地状态页显示 Hook 最近读取证据；该证据表示 Hook 读取过规则，不代表模型必然遵循。测试：`tests/test_codex_integration.py`。

## 模型接入与对话

- [x] Codex 通过 `UserPromptSubmit` Hook 注入 `additionalContext`。实现：`codex-plugin/hooks/user_prompt_submit.ps1`。
- [x] Claude 使用 Messages API，Gemini 使用 `generateContent`，DeepSeek 和豆包使用 OpenAI 兼容 Chat Completions。实现：`server/providers/`。测试：`tests/test_provider_adapters.py`。
- [x] 页面聊天通过 `/chat` 调用当前选定的适配器；人格启用时将当前人格规则放入 system 提示。
- [x] 人格切换时保留页面显示的对话记录和用户消息；网关最多处理最近 20 条历史消息。
- [x] 只有带有当前人格版本标记的助手历史会继续发送给模型；旧版本或缺少版本标记的助手回复会被过滤。用户历史消息继续保留。测试：`tests/test_chat_integration.py`。
- [x] 切换/发送期间校验人格版本，拒绝过期回复。测试：`tests/test_chat_integration.py`、`tests/test_state.py`。

## 提示词与历史边界

- [x] 每轮重新注入当前人格规则，并说明旧人格规则已撤销；保留与当前任务相关的用户事实和必要上下文。测试：`tests/test_chat_integration.py`、`tests/test_codex_integration.py`。
- [x] 不把旧人格助手发言作为新人格请求历史；页面已有可见记录不会因此删除。
- [x] Hook 不转发用户 prompt，也不读取模型 API Key。测试：`tests/test_codex_hook.py`。
- [x] `skills/read-current/` 和 `switcher/` 提供支持 Agent Skill 的对话内读取/切换流程；`CHAT_BOOTSTRAP.md` 提供手动粘贴使用方式。

## API 与安全

- [x] 提供 `/current`、`/switch`、`/enable`、`/context`、`/codex/context`、`/integration/status`、`/provider-defaults`、`/personas`、`/history`、`/reset`、`/chat` 等接口。实现：`server/main.py`。
- [x] API Key 按平台配置；用户指定自定义 API Base 时必须显式携带对应 Key，避免环境密钥跨域发送。测试：`tests/test_chat_security.py`。
- [x] API Base 拒绝账号密码、查询参数和片段；自定义人格拒绝越界路径与不安全符号链接。测试：`tests/test_chat_security.py`、`tests/test_persona_store.py`。
- [x] Codex Hook 使用本地随机令牌认证，并限制请求目标为本机地址。测试：`tests/test_runtime_config.py`、`tests/test_codex_hook.py`、`tests/test_codex_integration.py`。

## 界面

- [x] 人格控制台包含人格卡片、启用范围、平台选择、聊天区、人格状态、API 配置和自定义人格表单。测试：`tests/test_ui_contract.py`。
- [x] “生效规则”使用紧凑可访问提示；布局支持桌面、平板和手机。结构测试：`tests/test_ui_contract.py`；人工验收：以真实浏览器检查 1440×900 和 390×844，无横向溢出且控件可操作。
- [x] API 密钥按平台保存在当前浏览器 `localStorage`；共享设备不要保存密钥。

## 明确限制与风险

- [x] 人格是提示词层的引导，不修改模型权重，不能保证模型绝对遵循。
- [x] Codex 保留原聊天上下文。Hook 只能给后续提交追加新人格边界，不能从已有转录中删除过去注入的提示词；因此只能降低旧人格影响，不能保证彻底清除。
- [x] 当前页面 ID 按标签页区分，但服务端激活状态是单份共享状态；不同标签页分别改变作用域时会互相覆盖，不是多标签独立人格配置。
- [x] Claude、Gemini、DeepSeek 和豆包的官方网页不会自动接管；需要通过本项目网关/API 调用。Codex 通过 Hook 影响后续提交。
- [x] 当前为单用户本地应用，没有用户登录或多用户隔离。真实服务商 API 凭据下的端到端模型回复未纳入自动化测试，需用户自行配置并验证。
