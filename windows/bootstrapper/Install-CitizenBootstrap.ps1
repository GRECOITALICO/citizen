#Requires -Version 5.1
<#
.SYNOPSIS
  End-user Windows bootstrapper for Citizen 0.2.0 via WSL2.
  Orchestrates existing adapter scripts. Does not implement a native Citizen.exe.
#>
param(
  [string]$InstallRoot = "$env:ProgramData\CONRRAD\Citizen",
  [string]$Distro = "CONRRAD-Citizen",
  [string]$BaseDistro = "Ubuntu-24.04",
  [string]$LinuxInstallRoot = "/opt/conrrad-citizen",
  [string]$CitizenHome = "/home/citizen/.local/share/conrrad-citizen",
  [switch]$SkipLaunch
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WindowsDir = Split-Path -Parent $ScriptDir
$Detect = Join-Path $ScriptDir "Detect-CitizenPrerequisites.ps1"
$InstallAdapter = Join-Path $WindowsDir "Install-CitizenWsl2.ps1"
$AutoStart = Join-Path $WindowsDir "Register-CitizenAutoStart.ps1"
$Launch = Join-Path $WindowsDir "Launch-CitizenUI.ps1"

function Assert-NoCloudToolsRequired {
  # Installer must not invoke git/aws/az/gh. Those tools are not prerequisites.
}

function Enable-WslFeaturesIfNeeded {
  $needReboot = $false
  foreach ($feat in @("Microsoft-Windows-Subsystem-Linux", "VirtualMachinePlatform")) {
    try {
      $st = Get-WindowsOptionalFeature -Online -FeatureName $feat -ErrorAction Stop
      if ($st.State -ne "Enabled") {
        Write-Host "Enabling Windows feature $feat ..."
        Enable-WindowsOptionalFeature -Online -FeatureName $feat -NoRestart -All | Out-Null
        $needReboot = $true
      }
    } catch {
      Write-Host "WARN: could not query/enable $feat : $($_.Exception.Message)"
    }
  }
  if ($needReboot) {
    throw "WSL features were enabled. Reboot Windows, then double-click CitizenSetup again."
  }
}

function Ensure-Wsl2Default {
  if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    throw "wsl.exe still missing after feature enable. Reboot, then re-run CitizenSetup."
  }
  wsl.exe --set-default-version 2 | Out-Null
}

function Test-DistroExists([string]$Name) {
  $list = wsl.exe -l -q 2>&1 | Out-String
  $names = $list -split "[\r\n]+" | ForEach-Object { $_.Trim().Trim([char]0) } | Where-Object { $_ }
  return ($names -contains $Name)
}

function Ensure-CitizenDistro {
  if (Test-DistroExists $Distro) {
    Write-Host "OK: distro '$Distro' already registered (idempotent)"
    return
  }
  Write-Host "Installing WSL distro '$Distro' from '$BaseDistro'..."
  wsl.exe --install -d $BaseDistro -n $Distro --no-launch 2>&1 | Out-Host
  if (Test-DistroExists $Distro) { return }
  # Fallback: install base name then import a dedicated copy only if CONRRAD-Citizen still missing.
  wsl.exe --install -d $BaseDistro --no-launch 2>&1 | Out-Host
  if (-not (Test-DistroExists $Distro) -and (Test-DistroExists $BaseDistro)) {
    $dest = Join-Path $InstallRoot "wsl"
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    $export = Join-Path $env:TEMP "conrrad-citizen-base.tar"
    Write-Host "Exporting $BaseDistro to create dedicated '$Distro' (does not delete $BaseDistro)..."
    wsl.exe --export $BaseDistro $export
    wsl.exe --import $Distro $dest $export --version 2
    Remove-Item -Force $export -ErrorAction SilentlyContinue
  }
  if (-not (Test-DistroExists $Distro)) {
    throw "Could not register WSL2 distro '$Distro'. Enable nested virtualization, reboot, and retry. Do not use WSL1."
  }
}

function Install-PayloadIntoLinux {
  $tar = Get-ChildItem -Path $InstallRoot -Filter "citizen-*-windows-wsl2.tar.gz" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $tar) {
    $tar = Get-ChildItem -Path $ScriptDir -Filter "citizen-*-windows-wsl2.tar.gz" -ErrorAction SilentlyContinue | Select-Object -First 1
  }
  if (-not $tar) {
    throw "Citizen payload tar.gz not found next to the installer ($InstallRoot)."
  }
  $win = $tar.FullName
  Write-Host "Staging payload $($tar.Name) into $LinuxInstallRoot ..."
  $cmd = @"
set -euo pipefail
if [[ -f $LinuxInstallRoot/VERSION ]]; then
  echo "OK: payload already present at $LinuxInstallRoot"
  exit 0
fi
mkdir -p $LinuxInstallRoot
SRC=`$(wslpath -a '$($win.Replace("'", "'\\''"))')
tar -C $LinuxInstallRoot --strip-components=1 -xzf "`$SRC"
test -f $LinuxInstallRoot/VERSION
test -f $LinuxInstallRoot/windows/wsl2/setup.sh
"@
  wsl.exe -d $Distro --exec /bin/bash -lc $cmd
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to extract Citizen payload into the WSL Linux filesystem."
  }
}

function Invoke-LinuxSetup {
  $adapterArgs = @{
    Distro          = $Distro
    BaseDistro      = $BaseDistro
    RepoLinuxPath   = $LinuxInstallRoot
    CitizenHome     = $CitizenHome
  }
  Write-Host "Running certified adapter Install-CitizenWsl2.ps1 ..."
  & $InstallAdapter @adapterArgs
  if ($LASTEXITCODE -eq 3) {
    Write-Host "systemd just enabled — wsl --shutdown then retry setup once"
    wsl.exe --shutdown
    Start-Sleep -Seconds 8
    & $InstallAdapter @adapterArgs
  }
}

Assert-NoCloudToolsRequired
Write-Host "== CONRRAD Citizen 0.2.0 Windows bootstrapper =="
& $Detect
if ($LASTEXITCODE -eq 2) {
  Enable-WslFeaturesIfNeeded
  & $Detect
  if ($LASTEXITCODE -ne 0) { throw "Prerequisites still failing. See messages above." }
}

Ensure-Wsl2Default
Ensure-CitizenDistro
Install-PayloadIntoLinux
Invoke-LinuxSetup

Write-Host "Registering autostart (idempotent)..."
& $AutoStart -Distro $Distro

Write-Host "Verifying version authority inside WSL..."
$verify = wsl.exe -d $Distro --exec /bin/bash -lc @"
set -e
echo VERSION=`$(cat $LinuxInstallRoot/VERSION)
echo RUNTIME=`$(python3 -c "import sys; sys.path.insert(0,'$LinuxInstallRoot/runtime'); from citizen_seed import RUNTIME_VERSION; print(RUNTIME_VERSION)")
echo MANIFEST=`$(python3 -c "import json; print(json.load(open('$CitizenHome/manifest/current.json')).get('citizen_version','missing'))" 2>/dev/null || echo missing)
echo CURRENT=`$(cat $CitizenHome/ops/CURRENT_VERSION.txt 2>/dev/null || echo missing)
"@
Write-Host $verify

if (-not $SkipLaunch) {
  & $Launch -Distro $Distro
}

Write-Host "OK: Citizen Windows bootstrapper finished"
exit 0
