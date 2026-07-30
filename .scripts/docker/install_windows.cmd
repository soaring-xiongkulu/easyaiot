@echo off
REM EasyAIoT Windows deploy launcher (bypasses ExecutionPolicy for this script only)
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_windows.ps1" %*
exit /b %ERRORLEVEL%
