@echo off
chcp 65001 >nul
set PYTHON=C:\Users\Vur\AppData\Local\Programs\Python\Python310\python.exe
set FLAGS_use_mkldnn=0
set FLAGS_use_onednn=0
set PADDLE_USE_ONEDNN=0
cd /d "%~dp0"

echo ========================================
echo   GOST Processor
echo   Python: %PYTHON%
echo ========================================

%PYTHON% GOST.py %*
pause
