; script to make an dali_gui installer package for windows using NSIS

;--------------------------------

; The name of the installer
Name "hasseb DaliController2"

; The file to write
OutFile "install.exe"

; The default installation directory
InstallDir $PROGRAMFILES\hasseb\DaliController2

; Registry key to check for directory (so if you install again, it will 
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\hasseb_DaliController2" "Install_Dir"

; Request application privileges for Windows Vista
RequestExecutionLevel admin
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

  ; Set output path to the installation directory.
  SetOutPath $INSTDIR
  
  ; Put file there
  File dist\dali_gui.exe
  File hidapi.dll
  File hasseb_icon.ico
  
  ; Add install directory to path; Add a value
  EnVar::AddValue "PATH" $INSTDIR
  Pop $0
  DetailPrint "EnVar::AddValue returned=|$0|"
  
  ; Write the installation path into the registry
  WriteRegStr HKLM "Software\hasseb_DaliController2" "Install_Dir" "$INSTDIR"
  
  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DaliController2" "DisplayName" "hasseb DaliController2"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DaliController2" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DaliController2" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DaliController2" "NoRepair" 1
  WriteUninstaller "$INSTDIR\uninstall.exe"
  
SectionEnd

; Optional section (can be disabled by the user)
Section "Start Menu Shortcuts"

  CreateDirectory "$SMPROGRAMS\DaliController2"
  CreateShortcut "$SMPROGRAMS\DaliController2\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
  CreateShortcut "$SMPROGRAMS\DaliController2\DaliController2.lnk" "$INSTDIR\dali_gui.exe" "" "$INSTDIR\dali_gui.exe" 0
  
SectionEnd

Section "Desktop Shortcut"

  CreateShortCut "$DESKTOP\DaliController2.lnk" "$INSTDIR\dali_gui.exe" ""
  
SectionEnd

;--------------------------------

; Uninstaller

Section "Uninstall"
  
  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DaliController2"
  DeleteRegKey HKLM SOFTWARE\hasseb_DaliController2

  ; Remove files and uninstaller
  Delete "$INSTDIR\dali_gui.exe"
  Delete "$INSTDIR\hidapi.dll"
  Delete "$INSTDIR\hasseb_icon.ico"
  Delete "$INSTDIR\uninstall.exe"

  ; Remove shortcuts, if any
  Delete "$SMPROGRAMS\DaliController2\*.*"
  Delete "$DESKTOP\DaliController2.lnk"

  ; Remove directories used
  RMDir "$SMPROGRAMS\DaliController2"
  RMDir "$INSTDIR"
  
  ; Remove install directory from PATH
  ; Delete a value from a variable
  EnVar::DeleteValue "PATH" $INSTDIR
  Pop $0
  DetailPrint "EnVar::DeleteValue returned=|$0|"

SectionEnd
