Unicode true
ManifestDPIAware true

!define PRODUCT_NAME "uniTerm"
!define BINARY "uniTerm.exe"
!ifndef VERSION
  !define VERSION "dev"
!endif
!ifndef VCXSRV_DIR
  !define VCXSRV_DIR "plugins\vcxsrv"
!endif

Name "${PRODUCT_NAME}"
!ifdef ARG_WAILS_AMD64_BINARY
  OutFile "..\..\bin\uniTerm-amd64-installer.exe"
!else
  OutFile "..\..\bin\uniTerm-arm64-installer.exe"
!endif
InstallDir "$PROGRAMFILES64\${PRODUCT_NAME}"
RequestExecutionLevel admin
SetCompressor /SOLID lzma
SetCompressorDictSize 128

!include "MUI2.nsh"
!include "LogicLib.nsh"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\${BINARY}"
; Launch uniTerm via Explorer on finish-page "Run" so it never inherits the
; installer's elevated token. Admin is opted in explicitly by the user.
!define MUI_FINISHPAGE_RUN_FUNCTION "LaunchUnelevated"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

Function .onInit
  Call CheckAndCloseProcess
FunctionEnd

; Launch via Explorer (normal privileges) so uniTerm does not inherit the
; installer's elevated token.
Function LaunchUnelevated
  Exec 'explorer.exe "$INSTDIR\${BINARY}"'
FunctionEnd

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

; The wizard pages localize to the OS language, so the custom dialogs below
; must follow suit via LangString instead of hardcoded Chinese.
LangString MSG_FORCE_CLOSE_PROMPT ${LANG_SIMPCHINESE} "${PRODUCT_NAME} 正在运行。安装前需要先关闭它。是否强制关闭进程？"
LangString MSG_FORCE_CLOSE_PROMPT ${LANG_ENGLISH} "${PRODUCT_NAME} is currently running and must be closed before installing. Force-close the process?"
LangString MSG_CLOSE_MANUALLY ${LANG_SIMPCHINESE} "请手动关闭 ${PRODUCT_NAME} 后再继续安装。"
LangString MSG_CLOSE_MANUALLY ${LANG_ENGLISH} "Please close ${PRODUCT_NAME} manually and then continue installing."

Function CheckAndCloseProcess
  check_process:
  ; Use findstr to filter tasklist output: only match if process name appears in output
  nsExec::ExecToStack 'cmd /c tasklist /FI "IMAGENAME eq ${BINARY}" /NH 2>nul | findstr /I "${BINARY}"'
  Pop $0
  Pop $1
  ; findstr returns 0 only if the process name is found in output
  ${If} $0 != "0"
    Return
  ${EndIf}

  ; Process is running — ask user
  MessageBox MB_YESNO|MB_ICONQUESTION "$(MSG_FORCE_CLOSE_PROMPT)" /SD IDYES IDNO no_kill
  nsExec::ExecToStack 'cmd /c taskkill /F /IM "${BINARY}"'
  Pop $0
  Sleep 1500
  Goto check_process

  no_kill:
  MessageBox MB_OK|MB_ICONEXCLAMATION "$(MSG_CLOSE_MANUALLY)"
  Abort
FunctionEnd

Section "Install"
  SetOutPath "$INSTDIR"
!ifdef ARG_WAILS_AMD64_BINARY
  File "/oname=${BINARY}" "${ARG_WAILS_AMD64_BINARY}"
!else
  File "/oname=${BINARY}" "${ARG_WAILS_ARM64_BINARY}"
!endif
  SetOutPath "$INSTDIR\plugins\vcxsrv"
  File /r "${VCXSRV_DIR}\*"
  SetOutPath "$INSTDIR"
  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\${BINARY}"
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\${BINARY}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe"
  WriteUninstaller "$INSTDIR\uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayIcon" '"$INSTDIR\${BINARY}"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "Publisher" "uniTerm"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayVersion" "${VERSION}"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "NoRepair" 1
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\${BINARY}"
  Delete "$INSTDIR\uninstall.exe"
  RMDir /r "$INSTDIR\plugins\vcxsrv"
  RMDir "$INSTDIR\plugins"
  RMDir "$INSTDIR"
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk"
  RMDir "$SMPROGRAMS\${PRODUCT_NAME}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
SectionEnd
