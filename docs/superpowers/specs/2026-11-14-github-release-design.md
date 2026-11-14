# GitHub v0.3.0 发布设计

## 目的

把当前可运行的「第N人格」项目整理成一个可信、可复现、易上手的 GitHub 首次版本发布。

## 范围

- 优化 README 第一屏、安装路径和 Codex 接入说明。
- 增加 `CHANGELOG.md`，记录 v0.3.0 的功能边界与已知限制。
- 增加 `CONTRIBUTING.md`，说明本地验证和提交约定。
- 创建 annotated Git tag `v0.3.0`，并发布对应 GitHub Release。

## 非目标

- 不重写现有前端、FastAPI 或 Codex Hook。
- 不增加复杂 CI、自动发布、Issue 模板或安全扫描工作流。
- 不把 Codex Hook 误称为 Skill，也不宣称能修改模型本身。

## 架构说明

项目保持三层结构：人格目录中的 `SKILL.md` 提供人格规则；`codex-plugin/` 提供 Codex `UserPromptSubmit` Hook；`server/` 与 `index.html` 提供本地切换界面和 API。README 将明确说明三者的关系和限制。

## 验收标准

1. README 能在首屏说明项目是什么、适用范围、三分钟启动方式和 Codex 接入方式。
2. `CHANGELOG.md` 与 `CONTRIBUTING.md` 可独立阅读，且不包含密钥或本机运行状态。
3. 全量测试通过。
4. `v0.3.0` 标签和 GitHub Release 指向发布提交，远程 `main` 与本地一致。
