@echo off
chcp 936 >nul
cd /d "E:\MySQL\mysql-26.10.0-winx64\mysql-26.10.0-winx64\bin"
echo ============================================
echo   青禾志愿 MySQL 数据库
echo   本窗口请保持打开，关闭窗口即停止数据库
echo ============================================
mysqld.exe --console
pause
