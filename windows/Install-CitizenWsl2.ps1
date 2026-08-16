#Requires -Version 5.1
<#
.SYNOPSIS
  Bounded Windows entry: ensure WSL2 distro, run Linux-side Citizen setup.
  Does not implement a Windows-native Citizen runtime.
#>
param(
  [string]$Distro = "CONRRAD-Citizen",
  [string]$BaseDistro = "Ubuntu-24.04",
  [string]$RepoLinuxPath = "",
  [string]$CitizenHome = "/home/citizen/.local/share/conrrad-citizen"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Defaults = Join-Path $ScriptDir "wsl2\defaults.env"

function Test-Wsl2Available {
  if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    throw "wsl.exe not found. Install WSL2 before continuing."
  }
  $status = wsl.exe --status 2>&1 | Out-String
  if ($status -match "WSL1" -and $status -notmatch "WSL2") {
    throw "WSL1 detected. Set default version to 2: wsl --set-default-version 2"
  }
}

function Ensure-Distro {
  param([string]$Name, [string]$Base)
  $list = wsl.exe -l -v 2>&1 | Out-String
  if ($list -match [regex]::Escape($Name)) {
    Write-Host "OK: distro '$Name' already registered"
    return
  }
  Write-Host "Registering distro '$Name' from '$Base'..."
  wsl.exe --install -d $Base -n $Name
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to install/register WSL distro '$Name' from '$Base'"
  }
}

Test-Wsl2Available
Ensure-Distro -Name $Distro -Base $BaseDistro

if (-not $RepoLinuxPath) {
  throw "RepoLinuxPath required: clone citizen repo inside WSL Linux FS and pass path (not /mnt/c)."
}

$setupCmd = "CITIZEN_HOME=`"$CitizenHome`" bash `"$RepoLinuxPath/windows/wsl2/setup.sh`""
Write-Host "Running WSL setup in '$Distro'..."
wsl.exe -d $Distro --exec /bin/bash -lc $setupCmd
if ($LASTEXITCODE -ne 0) {
  throw "WSL setup failed (exit $LASTEXITCODE). If systemd was just enabled, run: wsl --shutdown, then retry."
}
Write-Host "OK: Install-CitizenWsl2 complete"
