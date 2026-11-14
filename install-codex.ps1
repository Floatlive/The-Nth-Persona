$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Codex = Get-Command codex -ErrorAction SilentlyContinue

if (-not $Codex) {
    throw "未找到 Codex CLI。请先安装 Codex，并确认 codex 命令可用。"
}

Write-Host "正在将第N人格本地插件源添加到 Codex..."
& $Codex.Source plugin marketplace add $Root
if ($LASTEXITCODE -ne 0) {
    throw "添加本地插件源失败。"
}

Write-Host "正在安装第N人格插件..."
& $Codex.Source plugin add "the-nth-persona@nth-persona-local"
if ($LASTEXITCODE -ne 0) {
    throw "安装第N人格插件失败。"
}

Write-Host ""
Write-Host "安装完成。请在 Codex 桌面端审阅并信任该插件的 UserPromptSubmit Hook。"
Write-Host "使用前先启动第N人格；之后页面切换会影响 Codex 后续提交。"
