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
    # Parse only the session id. Never forward, print, or store the submitted prompt.
    $rawInput = [Console]::In.ReadToEnd()
    $sessionId = $null
    if (-not [string]::IsNullOrWhiteSpace($rawInput)) {
        try {
            $eventData = $rawInput | ConvertFrom-Json
            $sessionId = [string]$eventData.session_id
        } catch {
            $sessionId = $null
        }
    }
    $url = $env:NTH_PERSONA_CODEX_URL
    $hookToken = $env:NTH_PERSONA_CODEX_TOKEN
    $configPath = Join-Path $env:LOCALAPPDATA "TheNthPersona\service.json"
    if (Test-Path -LiteralPath $configPath) {
        try {
            $config = Get-Content -Raw -Encoding UTF8 -LiteralPath $configPath | ConvertFrom-Json
            if (
                [string]::IsNullOrWhiteSpace($url) `
                    -and (Test-LocalContextUrl ([string]$config.codex_context_url))
            ) {
                $url = [string]$config.codex_context_url
            }
            if ([string]::IsNullOrWhiteSpace($hookToken)) {
                $hookToken = [string]$config.codex_hook_token
            }
        } catch {
            # 显式环境变量仍可工作；损坏配置不会覆盖它们。
        }
    }
    if ([string]::IsNullOrWhiteSpace($url)) {
        $url = "http://127.0.0.1:8000/codex/context"
    }
    if (-not (Test-LocalContextUrl $url)) {
        throw "人格服务地址必须是本机 HTTP 地址"
    }
    if ([string]::IsNullOrWhiteSpace($hookToken)) {
        throw "Codex Hook 本地令牌缺失"
    }
    $requestBody = @{ conversation_id = $sessionId } | ConvertTo-Json -Compress
    $response = Invoke-WebRequest `
        -Method Post `
        -Uri $url `
        -Headers @{ "X-Nth-Persona-Token" = $hookToken } `
        -ContentType "application/json; charset=utf-8" `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($requestBody)) `
        -TimeoutSec 3 `
        -UseBasicParsing
    $body = [System.Text.Encoding]::UTF8.GetString($response.RawContentStream.ToArray())
    $context = $body | ConvertFrom-Json
    if (($context.PSObject.Properties.Name -contains "active") -and -not [bool]$context.active) {
        Write-HookResult @{}
        exit 0
    }
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
