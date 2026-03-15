@echo off
chcp 65001 >nul
set PYTHON=C:\Users\Vur\AppData\Local\Programs\Python\Python310\python.exe
cd /d "%~dp0"

echo ========================================
echo   Сборка GOST Processor EXE
echo ========================================

%PYTHON% build_exe.py

echo.
if exist "dist\GOST_Processor\GOST_Processor.exe" (
    echo Копируем папку data...
    xcopy /s /y /i "data\*.pdf" "dist\GOST_Processor\data\" >nul 2>&1
    if not exist "dist\GOST_Processor\output" mkdir "dist\GOST_Processor\output"
    echo ========================================
    echo   ГОТОВО!
    echo   dist\GOST_Processor\GOST_Processor.exe
    echo ========================================
) else (
    echo ОШИБКА сборки!
)
pause
