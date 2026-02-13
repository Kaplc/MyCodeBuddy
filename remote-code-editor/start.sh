#!/bin/bash

echo "========================================"
echo "   远程代码编辑器 - 启动脚本"
echo "========================================"
echo

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到Python，请先安装Python 3.10+"
    exit 1
fi

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "[错误] 未找到Node.js，请先安装Node.js 18+"
    exit 1
fi

echo "[1/4] 安装后端依赖..."
cd backend
pip3 install -r requirements.txt

echo
echo "[2/4] 安装前端依赖..."
cd ../frontend
npm install

echo
echo "[3/4] 启动后端服务..."
cd ../backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo
echo "[4/4] 启动前端服务..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo
echo "========================================"
echo "服务已启动！"
echo "后端API: http://localhost:8000"
echo "前端界面: http://localhost:3000"
echo "========================================"
echo
echo "按Ctrl+C停止服务"

# 等待中断信号
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
wait
