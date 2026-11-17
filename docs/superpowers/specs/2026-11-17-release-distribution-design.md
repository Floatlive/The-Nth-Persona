# v0.4.3 发布包与升级识别设计

## 意图

让新用户能从 GitHub Releases 下载可启动的源码包，并确保已有 v0.4.2 服务不会被误判为当前版本。

## 方案

将应用版本提升到 0.4.3；Release 发布后由 GitHub Actions 从对应 Tag 生成版本化 Git 源码 ZIP 并附加到 Release。README 指向最新 Release，并说明附件生成期间可从主分支下载源码 ZIP。

源码包使用 `git archive`，只包含目标 Tag 中的已提交文件，不复制本地虚拟环境、运行状态、密钥或未跟踪文件。启动服务仍需 Python 3.10+；模型对话需用户自行配置对应 API 凭据。

## 非目标

- 本轮不创建或发布 GitHub Release。
- 不提供预装 Python、离线依赖或独立可执行程序。
- 不验证真实模型供应商 API。

## 验收

- 版本探测将 v0.4.2 服务识别为冲突，不能作为 v0.4.3 复用。
- Release 打包脚本为目标提交生成 `the-nth-persona-v0.4.3.zip`，ZIP 含启动入口、服务和人格规则，不含本机运行状态。
- GitHub Release 发布工作流将该 ZIP 上传为 Release 附件。
- 从生成的 ZIP 解压到干净临时目录后，本地服务可启动并通过 `/health`、`/version` 检查。
- README 的下载方式与 Release 附件实际产物一致。
