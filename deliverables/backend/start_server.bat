@echo off
chcp 936 >nul
cd /d "%~dp0"

set "MYSQL_DIR=E:\MySQL\mysql-26.10.0-winx64\mysql-26.10.0-winx64"

echo ============================================
echo   青禾志愿 后端启动器
echo ============================================

echo [1/2] 检查 MySQL...
netstat -an | findstr ":3306" | findstr "LISTENING" >nul
if errorlevel 1 (
    echo   MySQL 未运行，正在自动启动（会弹出 MySQL 窗口，请勿关闭）...
    start "MySQL" /min "%MYSQL_DIR%\bin\mysqld.exe" --defaults-file="%MYSQL_DIR%\my.ini"
    timeout /t 5 /nobreak >nul
) else (
    echo   MySQL 已运行
)

echo [2/2] 启动后端  http://127.0.0.1:8787/
echo.
python app.py

echo.
echo 服务已停止，按任意键关闭窗口...
pause >nul
