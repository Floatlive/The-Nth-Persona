# 贡献指南 · Contributing

感谢参与第N人格。项目当前优先服务个人本地使用，提交应保持小而清晰。

## 开发环境

要求：

- Python 3.10+
- Windows、macOS 或 Linux
- Git

创建虚拟环境并安装依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r server/requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

macOS / Linux：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r server/requirements.txt
.venv/bin/python -m pip install -r requirements-dev.txt
```

## 验证

提交前运行：

```powershell
.\.venv\Scripts\python.exe -m pytest
```

如果 pytest 默认临时目录权限异常，可以指定项目内临时目录：

```powershell
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp .pytest-local-check
```

macOS / Linux:

```bash
.venv/bin/python -m pytest -p no:cacheprovider --basetemp .pytest-local-check
```

## 修改边界

- 人格规则放在对应目录的 `SKILL.md`。
- Codex 接入只修改 `codex-plugin/` 和必要的后端接口。
- 不要把 API Key、`server/data/current.json`、`server/data/history.json`、`.venv`、缓存或本地日志提交到仓库。
- `xin-da-ya` 的完整「先信 → 再达 → 后雅」流程只属于 `xin-da-ya`。
- 不要把 Hook 描述为模型级控制；它是每轮提示上下文注入。

## 提交信息

推荐使用 Conventional Commits：

```text
feat: add a persona
fix: reject stale persona responses
docs: clarify Codex hook limits
test: cover state recovery
```

## Pull Request

请在 PR 中说明：

1. 改了什么，以及为什么改。
2. 影响了哪些运行路径。
3. 如何验证，附测试命令和结果。
4. 是否改变了用户可见行为或人格边界。
