@echo off
echo ========================================
echo    远程代码编辑器 - 启动脚本
echo ========================================
echo.

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.10+
    pause
    exit /b 1
)

:: 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Node.js，请先安装Node.js 18+
    pause
    exit /b 1
)

echo [1/4] 安装后端依赖...
cd backend
pip install -r requirements.txt

echo.
echo [2/4] 安装前端依赖...
cd ..\frontend
call npm install

echo.
echo [3/5] 清理旧进程（端口8000）...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo 正在终止进程 %%a ...
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo [3/5] 清理旧进程（端口8000）...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo 正在终止进程 %%a ...
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo [4/5] 启动后端服务...
cd ..\backend
start "Backend" cmd /k "python run_server.py"

echo.
echo [5/5] 启动前端服务...
cd ..\frontend
start "Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo 服务已启动！
echo 后端API: http://localhost:8000
echo 前端界面: http://localhost:3000
echo ========================================
echo.
echo 按任意键打开浏览器...
pause >nul
start http://localhost:3000
