#!/usr/bin/env bash
# 第N人格 · The Nth Persona — 一键安装依赖、启动、打开页面

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
PORT="${NTH_PORT:-8000}"
if [[ ! "$PORT" =~ ^[0-9]+$ ]] || (( PORT < 1 || PORT > 65535 )); then
  echo "NTH_PORT 必须是 1 到 65535 之间的整数。"
  exit 1
fi
URL="http://127.0.0.1:$PORT"
PROBE="$DIR/server/service_probe.py"

echo "=================================="
echo "  第N人格 · The Nth Persona"
echo "=================================="
echo ""

start_server() {
  cd "$DIR/server"
  nohup "$PY" -m uvicorn main:app --host 127.0.0.1 --port "$PORT" > /tmp/nth-persona.log 2>&1 &
  echo $! > /tmp/nth-persona.pid
  cd "$DIR"
  for i in 1 2 3 4 5 6 7 8 9 10; do
    sleep 0.4
    if "$PY" "$PROBE" "$URL" >/dev/null 2>&1; then
      return 0
    fi
  done
  return 1
}

if [[ -x "$DIR/.venv/bin/python" ]]; then
  SYSTEM_PY="$DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  SYSTEM_PY=python3
elif command -v python >/dev/null 2>&1; then
  SYSTEM_PY=python
else
  echo "未找到 Python 3，请先安装 Python 3.10 或更高版本。"
  exit 1
fi

if ! "$SYSTEM_PY" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
  echo "需要 Python 3.10 或更高版本。"
  exit 1
fi

set +e
"$SYSTEM_PY" "$PROBE" "$URL" >/dev/null 2>&1
SERVICE_STATUS=$?
set -e

if [[ "$SERVICE_STATUS" -eq 2 ]]; then
  echo "端口 $PORT 已被其他服务或旧版第N人格占用。"
  echo "请关闭占用服务，或使用其他端口，例如："
  echo "  NTH_PORT=8010 ./open.sh"
  exit 1
elif [[ "$SERVICE_STATUS" -eq 0 ]]; then
  echo "服务已在运行: $URL"
elif [[ "$SERVICE_STATUS" -eq 1 ]]; then

  # 项目级虚拟环境，避免污染用户的系统 Python。
  VENV_DIR="$DIR/.venv"
  PY="$VENV_DIR/bin/python"
  if [[ ! -x "$PY" ]]; then
    "$SYSTEM_PY" -m venv "$VENV_DIR"
  fi
  if ! "$PY" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "项目虚拟环境需要 Python 3.10 或更高版本，请删除 .venv 后重试。"
    exit 1
  fi

  # 首次或依赖缺失时安装。
  if ! "$PY" -c "import fastapi, uvicorn, httpx, pydantic" 2>/dev/null; then
    echo "首次运行：正在安装依赖 (fastapi / uvicorn / httpx / pydantic)..."
    "$PY" -m pip install -r "$DIR/server/requirements.txt"
    echo ""
  fi

  echo "正在启动服务..."
  if start_server; then
    echo "服务已启动: $URL"
  else
    echo "启动失败。日志: /tmp/nth-persona.log"
    echo "可手动执行:"
    echo "  cd server && $PY -m pip install -r requirements.txt"
    echo "  $PY -m uvicorn main:app --port $PORT"
    exit 1
  fi
else
  echo "无法确认本地服务状态，探测器退出码：$SERVICE_STATUS"
  exit 1
fi

echo ""
echo "正在打开页面..."
if [[ "$OSTYPE" == "darwin"* ]]; then
  open "$URL" 2>/dev/null || true
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
  cmd.exe /c start "$URL" 2>/dev/null || true
else
  xdg-open "$URL" 2>/dev/null || echo "请手动打开: $URL"
fi

echo ""
echo "页面: $URL"
echo "API 文档: $URL/docs"
echo "用法: 点击人格 → 立即显示「已切换至…」→ 设置里填 API Key 后对话"
echo "=================================="
