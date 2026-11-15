# 第N人格 · The Nth Persona — Windows 一键启动
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerDir = Join-Path $Root "server"
$VenvDir = Join-Path $Root ".venv"
$Python = Join-Path $VenvDir "Scripts\python.exe"
$ProbeScript = Join-Path $ServerDir "service_probe.py"
$RuntimeConfigScript = Join-Path $ServerDir "runtime_config.py"
$Port = 8000
if ($env:NTH_PORT) {
    $ParsedPort = 0
    if (-not [int]::TryParse($env:NTH_PORT, [ref]$ParsedPort) -or $ParsedPort -lt 1 -or $ParsedPort -gt 65535) {
        throw "NTH_PORT 必须是 1 到 65535 之间的整数。"
    }
    $Port = $ParsedPort
}
$Url = "http://127.0.0.1:$Port"
$RuntimeDir = Join-Path $Root ".runtime"
$Log = Join-Path $RuntimeDir "server.log"
$ErrorLog = Join-Path $RuntimeDir "server-error.log"

Set-Location $Root
New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

function Assert-PythonVersion {
    param([string]$Executable, [string[]]$Arguments = @())
    & $Executable @Arguments -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
    if ($LASTEXITCODE -ne 0) {
        throw "需要 Python 3.10 或更高版本。"
    }
}

if (Test-Path $Python) {
    $ProbePython = $Python
    $ProbeArguments = @()
} else {
    $SystemPython = Get-Command py -ErrorAction SilentlyContinue
    if ($SystemPython) {
        $ProbePython = $SystemPython.Source
        $ProbeArguments = @("-3")
    } else {
        $SystemPython = Get-Command python -ErrorAction SilentlyContinue
        if (-not $SystemPython) {
            Write-Host "未找到 Python 3。请先安装 Python 3.10 或更高版本，并勾选 Add Python to PATH。" -ForegroundColor Red
            Read-Host "按 Enter 退出"
            exit 1
        }
        $ProbePython = $SystemPython.Source
        $ProbeArguments = @()
    }
}

Assert-PythonVersion -Executable $ProbePython -Arguments $ProbeArguments

function Invoke-ServiceProbe {
    & $ProbePython @ProbeArguments $ProbeScript $Url | Out-Null
    return $LASTEXITCODE
}

function Exit-PortConflict {
    Write-Host "端口 $Port 已被其他服务或旧版第N人格占用。" -ForegroundColor Red
    Write-Host "请关闭占用该端口的服务，或先设置其他端口，例如：" -ForegroundColor Yellow
    Write-Host '  $env:NTH_PORT = "8010"; .\open.ps1'
    exit 1
}

$ServiceStatus = Invoke-ServiceProbe
if ($ServiceStatus -eq 2) {
    Exit-PortConflict
}
if ($ServiceStatus -notin @(0, 1)) {
    throw "无法确认本地服务状态，探测器退出码：$ServiceStatus"
}

if ($ServiceStatus -eq 1) {
    if (-not (Test-Path $Python)) {
        & $ProbePython @ProbeArguments -m venv $VenvDir
        if ($LASTEXITCODE -ne 0) { throw "创建 Python 虚拟环境失败。" }
    }

    if (-not (Test-Path $Python)) { throw "虚拟环境中的 Python 未找到：$Python" }

    Assert-PythonVersion -Executable $Python
    $ProbePython = $Python
    $ProbeArguments = @()

    $DependenciesReady = & $Python -c "import fastapi, uvicorn, httpx, pydantic" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "正在安装项目依赖..." -ForegroundColor Yellow
        & $Python -m pip install -r (Join-Path $ServerDir "requirements.txt")
        if ($LASTEXITCODE -ne 0) { throw "安装项目依赖失败。" }
    }

    $PreStartStatus = Invoke-ServiceProbe
    if ($PreStartStatus -eq 2) {
        Exit-PortConflict
    }
    if ($PreStartStatus -eq 1) {
        if (Test-Path $Log) { Remove-Item $Log -Force }
        if (Test-Path $ErrorLog) { Remove-Item $ErrorLog -Force }
        $Process = Start-Process -FilePath $Python `
            -ArgumentList @("-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "$Port") `
            -WorkingDirectory $ServerDir -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput $Log -RedirectStandardError $ErrorLog

        $Ready = $false
        for ($i = 0; $i -lt 40; $i++) {
            Start-Sleep -Milliseconds 500
            if ((Invoke-ServiceProbe) -eq 0) { $Ready = $true; break }
            if ($Process.HasExited) { break }
        }
        if (-not $Ready) {
            Write-Host "服务启动失败。日志位置：$Log" -ForegroundColor Red
            if (Test-Path $Log) { Get-Content $Log -Tail 20 }
            if (Test-Path $ErrorLog) { Get-Content $ErrorLog -Tail 20 }
            Read-Host "按 Enter 退出"
            exit 1
        }
    }
}

& $ProbePython @ProbeArguments $RuntimeConfigScript --url $Url | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "写入 Codex 本地服务配置失败。"
}

Write-Host "第N人格已启动：$Url" -ForegroundColor Green
Start-Process $Url
Write-Host "API 文档：$Url/docs"
Write-Host "关闭服务：在任务管理器中结束对应的 Python / uvicorn 进程。"
