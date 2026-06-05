@echo off
chcp 65001 > nul
title Tools Win V2

:: Verificar privilégios de Administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Solicitando permissão de Administrador...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:menu
cls
echo ====================================================
echo                   TOOLS WIN V2
echo ====================================================
echo.
echo [1] Executar Tools Win V2 (Interface Grafica Python)
echo [2] Compilar para Executavel (Gerar Tools Win V2.exe)
echo [3] Executar Versao Anterior (Powershell CLI)
echo [0] Sair
echo.
echo ====================================================
set /p opcao="Escolha uma opcao: "

if "%opcao%"=="1" (
    echo.
    echo [*] Iniciando aplicacao Python...
    python "%~dp0app.py"
    pause
    goto menu
)

if "%opcao%"=="2" (
    echo.
    echo [*] Iniciando compilacao do executavel...
    python "%~dp0build_exe.py"
    pause
    goto menu
)

if "%opcao%"=="3" (
    echo.
    echo [*] Executando script PowerShell anterior...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Normal -File "%~dp0WindowsOptimizer.ps1"
    pause
    goto menu
)

if "%opcao%"=="0" (
    exit
)

echo Opcao invalida!
timeout /t 2 >nul
goto menu