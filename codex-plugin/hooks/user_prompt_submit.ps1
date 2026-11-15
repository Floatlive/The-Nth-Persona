$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

function Write-HookResult {
    param([hashtable]$Result)
    [Console]::Out.WriteLine(($Result | ConvertTo-Json -Compress -Depth 6))
}

function Test-LocalContextUrl {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $false
    }
    try {
        $uri = [Uri]$Value
        return $uri.Scheme -eq "http" `
            -and $uri.Host -in @("127.0.0.1", "localhost") `
            -and $uri.AbsolutePath -eq "/codex/context"
    } catch {
        return $false
    }
}

try {
    # Hooks receive the submitted prompt on stdin. Consume it without forwarding or storing it.
    [void][Console]::In.ReadToEnd()
    $url = $env:NTH_PERSONA_CODEX_URL
    if ([string]::IsNullOrWhiteSpace($url)) {
        $configPath = Join-Path $env:LOCALAPPDATA "TheNthPersona\service.json"
        if (Test-Path -LiteralPath $configPath) {
            try {
                $config = Get-Content -Raw -Encoding UTF8 -LiteralPath $configPath | ConvertFrom-Json
                if (Test-LocalContextUrl ([string]$config.codex_context_url)) {
                    $url = [string]$config.codex_context_url
                }
            } catch {
                $url = $null
            }
        }
    }
    if ([string]::IsNullOrWhiteSpace($url)) {
        $url = "http://127.0.0.1:8000/codex/context"
    }
    if (-not (Test-LocalContextUrl $url)) {
        throw "人格服务地址必须是本机 HTTP 地址"
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
