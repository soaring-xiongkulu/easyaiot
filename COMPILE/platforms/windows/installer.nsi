; EasyAIoT PANEL Windows Installer (NSIS)
; 安装二进制 + panel.env + run.bat + 内置 runtime（install_windows 镜像部署）
!define APP_NAME "EasyAIoT Panel"
!define APP_EXE "easyaiot-panel.exe"
!define APP_VERSION "__VERSION__"

OutFile "__OUTFILE__"
InstallDir "$PROGRAMFILES64\EasyAIoT Panel"
RequestExecutionLevel admin
SetCompressor /SOLID lzma

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  File "__DISTDIR__\easyaiot-panel.exe"
  File "__DISTDIR__\panel.env.example"
  File /nonfatal "__DISTDIR__\panel.env"
  File "__DISTDIR__\run.bat"
  File /nonfatal "__DISTDIR__\README.txt"

  ; 内置 EasyAIoT runtime（.scripts + 模块 compose / install 脚本）
  SetOutPath "$INSTDIR\runtime"
  File /r "__DISTDIR__\runtime\*.*"

  CreateDirectory "$SMPROGRAMS\EasyAIoT Panel"
  CreateShortCut "$SMPROGRAMS\EasyAIoT Panel\EasyAIoT Panel.lnk" "$INSTDIR\run.bat"
  CreateShortCut "$DESKTOP\EasyAIoT Panel.lnk" "$INSTDIR\run.bat"

  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EasyAIoT Panel" "DisplayName" "${APP_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EasyAIoT Panel" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EasyAIoT Panel" "UninstallString" "$INSTDIR\uninstall.exe"
  WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$SMPROGRAMS\EasyAIoT Panel\EasyAIoT Panel.lnk"
  RMDir "$SMPROGRAMS\EasyAIoT Panel"
  Delete "$DESKTOP\EasyAIoT Panel.lnk"

  Delete "$INSTDIR\easyaiot-panel.exe"
  Delete "$INSTDIR\panel.env.example"
  Delete "$INSTDIR\panel.env"
  Delete "$INSTDIR\run.bat"
  Delete "$INSTDIR\README.txt"
  Delete "$INSTDIR\uninstall.exe"
  RMDir /r "$INSTDIR\runtime"
  RMDir "$INSTDIR"

  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EasyAIoT Panel"
SectionEnd
