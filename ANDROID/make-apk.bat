@echo off
setlocal enabledelayedexpansion

REM ================================================================
REM  EasyAIoT APK one-click build script (Windows)
REM  Usage:  make-apk.bat [prod|test|dev]     (default: prod)
REM  Output: ANDROID\easyaiot-<version>-<mode>-android.apk
REM  NOTE: keep this file ASCII only (cmd on zh-CN parses bat as GBK)
REM ================================================================

set MODE=%1
if "%MODE%"=="" set MODE=prod

for %%i in ("%~dp0.") do set ANDROID=%%~fi
for %%i in ("%ANDROID%\..") do set WORKSPACE=%%~fi
set FRONT=%WORKSPACE%\APP
set APPID=__UNI__8A5A71D

echo.
echo [1/5] Verify version consistency ...
set V_GRADLE=
set V_MANI=
set V_CTRL=
set C_GRADLE=
set C_MANI=
for /f "tokens=2" %%a in ('findstr /c:"versionName " "%ANDROID%\app\build.gradle"') do set V_GRADLE=%%a
set V_GRADLE=%V_GRADLE:"=%
for /f "tokens=2" %%a in ('findstr /c:"versionCode " "%ANDROID%\app\build.gradle"') do set C_GRADLE=%%a
for /f "tokens=2" %%a in ('findstr /c:"'versionName'" "%FRONT%\manifest.config.ts"') do set V_MANI=%%a
set V_MANI=%V_MANI:'=%
set V_MANI=%V_MANI:,=%
for /f "tokens=2" %%a in ('findstr /c:"'versionCode'" "%FRONT%\manifest.config.ts"') do set C_MANI=%%a
set C_MANI=%C_MANI:'=%
set C_MANI=%C_MANI:,=%
for /f "tokens=5 delims==/ " %%a in ('findstr /i /c:"appver" "%ANDROID%\app\src\main\assets\data\dcloud_control.xml"') do set V_CTRL=%%a
set V_CTRL=%V_CTRL:"=%
echo     gradle=%V_GRADLE%/%C_GRADLE%  manifest=%V_MANI%/%C_MANI%  dcloud=%V_CTRL%
if not defined V_GRADLE goto :verfail
if not defined V_MANI   goto :verfail
if not defined V_CTRL   goto :verfail
if not defined C_GRADLE goto :verfail
if not "%V_GRADLE%"=="%V_MANI%" goto :verfail
if not "%V_GRADLE%"=="%V_CTRL%" goto :verfail
if not "%C_GRADLE%"=="%C_MANI%"  goto :verfail

echo.
echo [2/5] Build frontend app resources (mode=%MODE%) ...
cd /d "%FRONT%"
if "%MODE%"=="prod"        ( call pnpm build:app:prod
) else if "%MODE%"=="test" ( call pnpm build:app:test
) else                     ( call pnpm build:app )
if errorlevel 1 goto :fail

echo.
echo [3/5] Sync www resources into android shell (%APPID%) ...
set SRC=%FRONT%\dist\build\app
set DST=%ANDROID%\app\src\main\assets\apps\%APPID%\www
if not exist "%SRC%\manifest.json" (
  echo [ERROR] %SRC%\manifest.json not found, frontend build may have failed
  goto :fail
)
findstr /c:"%V_GRADLE%" "%SRC%\manifest.json" >nul 2>&1
if errorlevel 1 (
  echo [ERROR] built manifest.json has no version %V_GRADLE%, output looks stale
  goto :fail
)
if exist "%DST%" rmdir /s /q "%DST%"
xcopy "%SRC%" "%DST%" /e /i /q >nul
if errorlevel 1 goto :fail

echo.
echo [4/5] Gradle assembleRelease ...
cd /d "%ANDROID%"
call gradlew.bat assembleRelease --no-daemon -Dorg.gradle.jvmargs=-Xmx3g
if errorlevel 1 goto :fail

if not exist "app\build\outputs\apk\release\app-release.apk" (
  echo [ERROR] apk output not found
  goto :fail
)
copy /y "app\build\outputs\apk\release\app-release.apk" "easyaiot-%V_GRADLE%-%MODE%-android.apk" >nul

echo.
echo ================================================================
echo  SUCCESS: %ANDROID%\easyaiot-%V_GRADLE%-%MODE%-android.apk
echo  signer: iot.jks (alias=iot)   package: com.basiclab.iot.app
echo ================================================================
goto :eof

:verfail
echo.
echo ==== VERSION MISMATCH - packaging aborted ====
echo Keep these three places identical:
echo   1. ANDROID\app\build.gradle                              versionName / versionCode
echo   2. APP\manifest.config.ts                                'versionName' / 'versionCode'
echo   3. ANDROID\app\src\main\assets\data\dcloud_control.xml   appver
goto :fail

:fail
echo.
echo ==== BUILD FAILED, check log above ====
exit /b 1
