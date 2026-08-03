; EasyAIoT PANEL Windows Installer (NSIS)
; Installs binary + panel.env + run.bat/run.vbs + bundled runtime (install_windows image deploy)
Unicode true
!define APP_NAME "EasyAIoT Panel"
!define APP_EXE "easyaiot-panel.exe"
!define APP_VERSION "__VERSION__"

OutFile "__OUTFILE__"
InstallDir "$PROGRAMFILES64\EasyAIoT Panel"
RequestExecutionLevel admin
SetCompressor /SOLID lzma
Icon "__DISTDIR__\panel.ico"
UninstallIcon "__DISTDIR__\panel.ico"

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  File "__DISTDIR__\easyaiot-panel.exe"
  File "__DISTDIR__\panel.ico"
  File "__DISTDIR__\panel.env.example"
  File /nonfatal "__DISTDIR__\panel.env"
  File "__DISTDIR__\run.bat"
  File "__DISTDIR__\run.vbs"
  File /nonfatal "__DISTDIR__\README.txt"

  ; 前端静态资源（exe 同级，不依赖 PyInstaller 临时解压目录）
  SetOutPath "$INSTDIR\ui"
  File /r "__DISTDIR__\ui\*.*"

  ; Bundled EasyAIoT runtime (.scripts + module compose / install scripts)
  SetOutPath "$INSTDIR\runtime"
  File /r "__DISTDIR__\runtime\*.*"

  ; SetOutPath 会影响快捷方式工作目录；切回安装根，避免 WD=runtime
  SetOutPath "$INSTDIR"
  CreateDirectory "$SMPROGRAMS\EasyAIoT Panel"
  ; 快捷方式指向 run.vbs：无黑窗；图标用 panel.ico
  CreateShortCut "$SMPROGRAMS\EasyAIoT Panel\EasyAIoT Panel.lnk" "$INSTDIR\run.vbs" "" "$INSTDIR\panel.ico" 0
  CreateShortCut "$DESKTOP\EasyAIoT Panel.lnk" "$INSTDIR\run.vbs" "" "$INSTDIR\panel.ico" 0

  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EasyAIoT Panel" "DisplayName" "${APP_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EasyAIoT Panel" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EasyAIoT Panel" "DisplayIcon" "$INSTDIR\easyaiot-panel.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EasyAIoT Panel" "UninstallString" "$INSTDIR\uninstall.exe"
  WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$SMPROGRAMS\EasyAIoT Panel\EasyAIoT Panel.lnk"
  RMDir "$SMPROGRAMS\EasyAIoT Panel"
  Delete "$DESKTOP\EasyAIoT Panel.lnk"

  Delete "$INSTDIR\easyaiot-panel.exe"
  Delete "$INSTDIR\panel.ico"
  Delete "$INSTDIR\panel.env.example"
  Delete "$INSTDIR\panel.env"
  Delete "$INSTDIR\run.bat"
  Delete "$INSTDIR\run.vbs"
  Delete "$INSTDIR\README.txt"
  Delete "$INSTDIR\uninstall.exe"
  RMDir /r "$INSTDIR\ui"
  RMDir /r "$INSTDIR\runtime"
  RMDir "$INSTDIR"

  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EasyAIoT Panel"
SectionEnd
