#Requires -Version 5.1
<#
.SYNOPSIS
  Safe uninstall of the Citizen WSL2 adapter integration.
  Never unregisters unrelated WSL distributions unless they are exactly CONRRAD-Citizen
  and -RemoveCitizenDistro is passed.
#>
param(
  [string]$Distro = "CONRRAD-Citizen",
  [string]$TaskName = "CONRRAD-Citizen-WSL2-Autostart",
  [string]$InstallRoot = "$env:ProgramData\CONRRAD\Citizen",
  [string]$Unit = "citizen-seed-living.service",
  [switch]$RemoveCitizenDistro,
  [switch]$RemoveCitizenHome
)

$ErrorActionPreference = "Stop"
$protected = @("Ubuntu", "Ubuntu-22.04", "Ubuntu-24.04", "docker-desktop", "docker-desktop-data")

if ($RemoveCitizenDistro -and ($protected -contains $Distro)) {
  throw "Refusing to unregister protected distro '$Distro'."
}

Write-Host "Stopping Citizen unit inside '$Distro' (best-effort)..."
if (Get-Command wsl.exe -ErrorAction SilentlyContinue) {
  wsl.exe -d $Distro --exec /bin/bash -lc "systemctl --user disable --now $Unit 2>/dev/null || true" 2>$null | Out-Null
}

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
  Write-Host "OK: removed scheduled task '$TaskName'"
} else {
  Write-Host "OK: scheduled task '$TaskName' not present"
}

if ($RemoveCitizenHome) {
  wsl.exe -d $Distro --exec /bin/bash -lc "rm -rf /home/citizen/.local/share/conrrad-citizen /root/.local/share/conrrad-citizen" 2>$null | Out-Null
  Write-Host "OK: removed Citizen home inside distro"
}

if ($RemoveCitizenDistro) {
  if ($Distro -ne "CONRRAD-Citizen") {
    throw "Refusing to unregister '$Distro' (only CONRRAD-Citizen may be removed by this uninstaller)."
  }
  wsl.exe --unregister $Distro
  Write-Host "OK: unregistered distro '$Distro'"
} else {
  Write-Host "OK: left WSL distros in place (pass -RemoveCitizenDistro to remove only CONRRAD-Citizen)"
}

if (Test-Path $InstallRoot) {
  Remove-Item -Recurse -Force $InstallRoot
  Write-Host "OK: removed $InstallRoot"
}

Write-Host "OK: uninstall complete"
exit 0
