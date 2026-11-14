# 第N人格 · The Nth Persona — Windows 一键启动
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerDir = Join-Path $Root "server"
$VenvDir = Join-Path $Root ".venv"
$Python = Join-Path $VenvDir "Scripts\python.exe"
$Url = "http://127.0.0.1:8000"
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

function Test-Service {
    try {
        $r = Invoke-WebRequest -Uri "$Url/health" -TimeoutSec 2 -UseBasicParsing
        return ($r.StatusCode -eq 200)
    } catch {
        return $false
    }
}

if (-not (Test-Service)) {
    if (-not (Test-Path $Python)) {
        $SystemPython = Get-Command py -ErrorAction SilentlyContinue
        if ($SystemPython) {
            Assert-PythonVersion -Executable $SystemPython.Source -Arguments @("-3")
            & $SystemPython.Source -3 -m venv $VenvDir
        } else {
            $SystemPython = Get-Command python -ErrorAction SilentlyContinue
            if (-not $SystemPython) {
                Write-Host "未找到 Python 3。请先安装 Python 3.10 或更高版本，并勾选 Add Python to PATH。" -ForegroundColor Red
                Read-Host "按 Enter 退出"
                exit 1
            }
            Assert-PythonVersion -Executable $SystemPython.Source
            & $SystemPython.Source -m venv $VenvDir
        }
        if ($LASTEXITCODE -ne 0) { throw "创建 Python 虚拟环境失败。" }
    }

    if (-not (Test-Path $Python)) { throw "虚拟环境中的 Python 未找到：$Python" }

    Assert-PythonVersion -Executable $Python

    $DependenciesReady = & $Python -c "import fastapi, uvicorn, httpx, pydantic" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "正在安装项目依赖..." -ForegroundColor Yellow
        & $Python -m pip install -r (Join-Path $ServerDir "requirements.txt")
        if ($LASTEXITCODE -ne 0) { throw "安装项目依赖失败。" }
    }

    if (-not (Test-Service)) {
        if (Test-Path $Log) { Remove-Item $Log -Force }
        if (Test-Path $ErrorLog) { Remove-Item $ErrorLog -Force }
        $Process = Start-Process -FilePath $Python `
            -ArgumentList @("-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000") `
            -WorkingDirectory $ServerDir -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput $Log -RedirectStandardError $ErrorLog

        $Ready = $false
        for ($i = 0; $i -lt 40; $i++) {
            Start-Sleep -Milliseconds 500
            if (Test-Service) { $Ready = $true; break }
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

Write-Host "第N人格已启动：$Url" -ForegroundColor Green
Start-Process $Url
Write-Host "API 文档：$Url/docs"
Write-Host "关闭服务：在任务管理器中结束对应的 Python / uvicorn 进程。"
