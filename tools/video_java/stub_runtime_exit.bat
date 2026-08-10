@echo off
REM Phase 0 stub RUNTIME — exits quickly to exercise unexpected-exit auto-restart
ping -n 2 127.0.0.1 >nul
exit /b 1
