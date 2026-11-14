$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

function Write-HookResult {
    param([hashtable]$Result)
    [Console]::Out.WriteLine(($Result | ConvertTo-Json -Compress -Depth 6))
}

try {
    # Hooks receive the submitted prompt on stdin. Consume it without forwarding or storing it.
    [void][Console]::In.ReadToEnd()
    $url = $env:NTH_PERSONA_CODEX_URL
    if ([string]::IsNullOrWhiteSpace($url)) {
        $url = "http://127.0.0.1:8000/codex/context"
    }
    $response = Invoke-WebRequest -Method Get -Uri $url -TimeoutSec 3 -UseBasicParsing
    $body = [System.Text.Encoding]::UTF8.GetString($response.RawContentStream.ToArray())
    $context = $body | ConvertFrom-Json
    if ([string]::IsNullOrWhiteSpace([string]$context.additional_context)) {
        throw "人格上下文为空"
    }
    $result = @{
        hookSpecificOutput = [ordered]@{
            hookEventName = "UserPromptSubmit"
            additionalContext = [string]$context.additional_context
        }
    }
    Write-HookResult $result
} catch {
    $result = @{
        systemMessage = "第N人格服务未连接，本轮未注入当前人格。请先启动第N人格应用，再重新提交。"
    }
    Write-HookResult $result
}
