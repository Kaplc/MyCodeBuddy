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

echo "[1/5] 检查环境配置文件..."
cd backend
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "[提示] 未找到 .env 文件，正在从模板创建..."
        cp .env.example .env
        echo "[成功] 已创建 .env 文件"
        echo "[警告] 请编辑 backend/.env 文件并填入真实的 API 密钥"
        echo
    else
        echo "[警告] 未找到 .env 和 .env.example 文件"
        echo
    fi
fi

echo
echo "[2/5] 安装后端依赖..."
pip3 install -r requirements.txt

echo
echo "[3/5] 安装前端依赖..."
cd ../frontend
npm install

echo
echo "[4/5] 启动后端服务..."
cd ../backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo
echo "[5/5] 启动前端服务..."
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
