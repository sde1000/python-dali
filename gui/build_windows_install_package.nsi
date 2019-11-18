; script to make an Dali2Controller installer package for windows using NSIS

;--------------------------------

; The name of the installer
Name "hasseb Dali2Controller"

; The file to write
OutFile "install.exe"

; The default installation directory
InstallDir $PROGRAMFILES\hasseb\Dali2Controller

; Registry key to check for directory (so if you install again, it will 
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\hasseb_Dali2Controller" "Install_Dir"

; Request admin privileges
RequestExecutionLevel admin

; Show installation details
ShowInstDetails Show

;--------------------------------

; Pages

Page components
Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

;--------------------------------

; The stuff to install
Section "" ;No components page, name is not important

  ; Set output path to the installation directory
  SetOutPath $INSTDIR
  
  ; Put file there
  File dist\dali_gui.exe
  File hidapi.dll
  File hasseb_icon.ico
  
  ; Add install directory to path
  EnVar::AddValue "PATH" $INSTDIR
  Pop $0
  DetailPrint "EnVar::AddValue returned=|$0|"
  
  ; Write the installation path into the registry
  WriteRegStr HKLM "Software\hasseb_Dali2Controller" "Install_Dir" "$INSTDIR"
  
  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Dali2Controller" "DisplayName" "hasseb Dali2Controller"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Dali2Controller" "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Dali2Controller" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Dali2Controller" "NoRepair" 1
  WriteUninstaller "$INSTDIR\uninstall.exe"
  
SectionEnd

; Optional section (can be disabled by the user)
Section "Start Menu Shortcuts"

  CreateDirectory "$SMPROGRAMS\Dali2Controller"
  CreateShortcut "$SMPROGRAMS\Dali2Controller\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
  CreateShortcut "$SMPROGRAMS\Dali2Controller\Dali2Controller.lnk" "$INSTDIR\dali_gui.exe" "" "$INSTDIR\dali_gui.exe" 0
  
SectionEnd

Section "Desktop Shortcut"

  CreateShortCut "$DESKTOP\Dali2Controller.lnk" "$INSTDIR\dali_gui.exe" ""
  
SectionEnd

;--------------------------------

; Uninstaller

Section "Uninstall"
  
  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Dali2Controller"
  DeleteRegKey HKLM SOFTWARE\hasseb_Dali2Controller

  ; Remove files and uninstaller
  Delete "$INSTDIR\dali_gui.exe"
  Delete "$INSTDIR\hidapi.dll"
  Delete "$INSTDIR\hasseb_icon.ico"
  Delete "$INSTDIR\uninstall.exe"

  ; Remove shortcuts, if any
  Delete "$SMPROGRAMS\Dali2Controller\*.*"
  Delete "$DESKTOP\Dali2Controller.lnk"

  ; Remove directories used
  RMDir "$SMPROGRAMS\Dali2Controller"
  RMDir "$INSTDIR"
  
  ; Remove install directory from PATH
  EnVar::DeleteValue "PATH" $INSTDIR
  Pop $0
  DetailPrint "EnVar::DeleteValue returned=|$0|"

SectionEnd
