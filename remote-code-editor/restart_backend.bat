@echo off
cd /d %~dp0backend
echo Starting backend server...
python run_server.py
pause
