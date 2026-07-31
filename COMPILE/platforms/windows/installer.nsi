; EasyAIoT PANEL Windows Installer (NSIS)
; Installs binary + panel.env + run.bat + bundled runtime (install_windows image deploy)
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
  File /nonfatal "__DISTDIR__\README.txt"

  ; Bundled EasyAIoT runtime (.scripts + module compose / install scripts)
  SetOutPath "$INSTDIR\runtime"
  File /r "__DISTDIR__\runtime\*.*"

  CreateDirectory "$SMPROGRAMS\EasyAIoT Panel"
  ; 4th arg = icon file (run.bat itself has no icon)
  CreateShortCut "$SMPROGRAMS\EasyAIoT Panel\EasyAIoT Panel.lnk" "$INSTDIR\run.bat" "" "$INSTDIR\panel.ico" 0
  CreateShortCut "$DESKTOP\EasyAIoT Panel.lnk" "$INSTDIR\run.bat" "" "$INSTDIR\panel.ico" 0

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
  Delete "$INSTDIR\README.txt"
  Delete "$INSTDIR\uninstall.exe"
  RMDir /r "$INSTDIR\runtime"
  RMDir "$INSTDIR"

  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EasyAIoT Panel"
SectionEnd
