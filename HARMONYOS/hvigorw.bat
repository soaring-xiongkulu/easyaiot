@echo off
rem ================================================================
rem HarmonyOS build launcher: locate and invoke hvigor.
rem Note: keep this file ASCII-only, zh-CN cmd parses bat as GBK
rem ================================================================
setlocal enabledelayedexpansion

if defined HVIGOR_HOME if exist "%HVIGOR_HOME%\bin\hvigorw.js" (
  node "%HVIGOR_HOME%\bin\hvigorw.js" %*
  exit /b !errorlevel!
)

for %%P in (
  "%ProgramFiles%\Huawei\DevEco Studio\tools\hvigor\bin\hvigorw.js"
  "%LOCALAPPDATA%\Huawei\DevEco Studio\tools\hvigor\bin\hvigorw.js"
  "%USERPROFILE%\AppData\Local\Programs\DevEco Studio\tools\hvigor\bin\hvigorw.js"
) do (
  if exist %%P (
    node %%P %*
    exit /b !errorlevel!
  )
)

where hvigorw >nul 2>nul
if !errorlevel! equ 0 (
  call hvigorw %*
  exit /b !errorlevel!
)

echo [ERROR] hvigor not found. It is distributed with DevEco Studio (no public npm package).
echo Set HVIGOR_HOME to DevEco Studio's tools\hvigor, or run make-hap.sh on a DevEco machine.
exit /b 1
