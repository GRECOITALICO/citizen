; Citizen 0.2.0 Windows WSL2 bootstrapper
; Built by scripts/build_windows_bootstrapper.py — not a public release.

!ifndef CITIZEN_VERSION
  !define CITIZEN_VERSION "0.2.0"
!endif
!ifndef BOOTSTRAPPER_VERSION
  !define BOOTSTRAPPER_VERSION "0.2.0-wsl2-bootstrapper.1"
!endif
!ifndef PAYLOAD_TAR
  !error "PAYLOAD_TAR must be defined"
!endif
!ifndef BOOTSTRAPPER_DIR
  !error "BOOTSTRAPPER_DIR must be defined"
!endif
!ifndef WINDOWS_DIR
  !error "WINDOWS_DIR must be defined"
!endif
!ifndef OUTFILE
  !error "OUTFILE must be defined"
!endif

Name "CONRRAD Citizen ${CITIZEN_VERSION}"
OutFile "${OUTFILE}"
InstallDir "$PROGRAMDATA\CONRRAD\Citizen"
RequestExecutionLevel admin
SetCompressor /SOLID lzma
Unicode true
ShowInstDetails show
CRCCheck on

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  File "${PAYLOAD_TAR}"
  SetOutPath "$INSTDIR\windows"
  File "${WINDOWS_DIR}\Install-CitizenWsl2.ps1"
  File "${WINDOWS_DIR}\Launch-CitizenUI.ps1"
  File "${WINDOWS_DIR}\Register-CitizenAutoStart.ps1"
  SetOutPath "$INSTDIR\windows\bootstrapper"
  File "${BOOTSTRAPPER_DIR}\Detect-CitizenPrerequisites.ps1"
  File "${BOOTSTRAPPER_DIR}\Install-CitizenBootstrap.ps1"
  File "${BOOTSTRAPPER_DIR}\Uninstall-CitizenWsl2.ps1"
  WriteUninstaller "$INSTDIR\Uninstall-Citizen.exe"
  CreateDirectory "$SMPROGRAMS\CONRRAD Citizen"
  CreateShortCut "$SMPROGRAMS\CONRRAD Citizen\Citizen.lnk" "powershell.exe" "-NoProfile -ExecutionPolicy Bypass -File $\"$INSTDIR\windows\Launch-CitizenUI.ps1$\""
  CreateShortCut "$SMPROGRAMS\CONRRAD Citizen\Uninstall Citizen.lnk" "$INSTDIR\Uninstall-Citizen.exe"
  DetailPrint "Running Citizen WSL2 bootstrapper..."
  nsExec::ExecToLog 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\windows\bootstrapper\Install-CitizenBootstrap.ps1" -InstallRoot "$INSTDIR"'
  Pop $0
  DetailPrint "Bootstrapper exit code $0"
SectionEnd

Section "Uninstall"
  nsExec::ExecToLog 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\windows\bootstrapper\Uninstall-CitizenWsl2.ps1" -InstallRoot "$INSTDIR"'
  Pop $0
  RMDir /r "$SMPROGRAMS\CONRRAD Citizen"
  Delete "$INSTDIR\Uninstall-Citizen.exe"
  RMDir /r "$INSTDIR"
SectionEnd
