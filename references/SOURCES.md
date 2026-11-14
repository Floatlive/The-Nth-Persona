# 参考来源 · 本项目借鉴的 GitHub 实践

本文件记录 v0.2.3 优化时参考的公开仓库与原则（非代码复制，仅模式借鉴）。

## 核心参考

| 仓库 | 可借鉴点 |
|------|----------|
| [anthropics/skills](https://github.com/anthropics/skills) | SKILL.md 标准：`name` + `description`；description 含触发条件（Use when…） |
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | 人格 = 单一角色 + 单一输出格式；**人格不互相调用**；Composition 由用户/命令完成 |
| [migueldeguzman/persona](https://github.com/migueldeguzman/persona) | 身份/记忆分层；持久化与 reflect；切换时完整覆盖 |
| [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) | Persona：性格 + **永远不做**；out of scope；vibe 一句话 |
| [praxstack/skills-and-personas](https://github.com/praxstack/skills-and-personas) | 反模式纪律；安全边界；技能宜短、可测 |

## 已吸收到第N人格的规则

1. **单一激活**：同一时间只一个人设（对标「persona 不互相 spawn」）
2. **description 触发面**：frontmatter 写清「当用户说…时必须启用」
3. **Never / 禁止**：每人格显式「永远不做」
4. **范围外处理**：超出职责时收束，不硬演
5. **示例输出**：每人格附简短对话样例，减少跑偏
6. **质量底线轻量共享，完整信达雅流程独占**

## 未照搬（刻意）

- 完整 MEMORY.md / 日记系统（本项目用 current.json + 对话历史分析即可）
- 多人格同时编排的 team 模式（与「单人格强制覆盖」冲突）

## v0.2.9 方案核查

| 来源 | 本次核查点 | 采用结论 |
|------|------------|----------|
| [FastAPI TrustedHostMiddleware](https://fastapi.tiangolo.com/advanced/middleware/) | 本地服务仍可能收到伪造 Host 头 | 增加 `127.0.0.1` / `localhost` 白名单 |
| [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/) | 路由与安全边界应有可重复回归测试 | 增加 `pytest` 测试入口；当前测试通过 HTTPX ASGI transport 调用真实应用 |
| [Open WebUI Models](https://github.com/open-webui/docs/blob/main/docs/features/workspace/models.md) | 人格提示与模型配置解耦 | 暂不引入大型模型注册层，保留本地 Skill + API 设置的轻量边界 |
| [SillyTavern Personas](https://github.com/SillyTavern/SillyTavern-Docs/blob/main/Usage/personas.md) | 人格可绑定到聊天上下文、支持锁定与备份 | 作为后续“按会话保存人格 / 导入导出”的设计参考，不在本次小版本扩张范围 |
