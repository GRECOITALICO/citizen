# Install Citizen 0.2 as a Windows Service (NSSM or sc.exe fallback).
# Requires: PowerShell, python on PATH, optional NSSM for robust service wrap.
# Does not modify Runtime / Foundation / GENESIS / Citizen Life / Papers.

param(
  [string]$SeedRoot = "",
  [string]$CitizenHome = "",
  [string]$Port = "3434",
  [string]$HostBind = "127.0.0.1",
  [string]$ServiceName = "CitizenSeedLiving"
)

$ErrorActionPreference = "Stop"

if (-not $SeedRoot) {
  $here = Split-Path -Parent $MyInvocation.MyCommand.Path
  $candidate = Join-Path $here "..\citizen-seed"
  if (Test-Path (Join-Path $candidate "ops\living_server.py")) {
    $SeedRoot = (Resolve-Path $candidate).Path
  } else {
    throw "Set -SeedRoot to citizen-seed directory"
  }
}

if (-not $CitizenHome) {
  $CitizenHome = Join-Path $SeedRoot ".citizen"
}

$pyCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pyCmd) { $pyCmd = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $pyCmd) { throw "python/python3 not found on PATH" }
$py = $pyCmd.Source

$living = Join-Path $SeedRoot "ops\living_server.py"
if (-not (Test-Path $living)) { throw "missing $living" }

New-Item -ItemType Directory -Force -Path (Join-Path $CitizenHome "ops") | Out-Null

$envBlock = @(
  "CITIZEN_HOME=$CitizenHome",
  "CITIZEN_UI_HOST=$HostBind",
  "CITIZEN_UI_PORT=$Port",
  "CITIZEN_OPEN_BROWSER=0",
  "PYTHONPATH=$(Join-Path $SeedRoot 'runtime')"
) -join ";"

$nssm = Get-Command nssm -ErrorAction SilentlyContinue
if ($nssm) {
  & nssm stop $ServiceName 2>$null
  & nssm remove $ServiceName confirm 2>$null
  & nssm install $ServiceName $py $living
  & nssm set $ServiceName AppDirectory $SeedRoot
  & nssm set $ServiceName AppEnvironmentExtra $envBlock
  & nssm set $ServiceName Start SERVICE_AUTO_START
  & nssm start $ServiceName
  Write-Host "Installed Windows service via NSSM: $ServiceName"
} else {
  # Minimal sc create — requires admin; uses cmd wrapper for env
  $wrapper = Join-Path $CitizenHome "ops\start_living.cmd"
  @"
@echo off
set CITIZEN_HOME=$CitizenHome
set CITIZEN_UI_HOST=$HostBind
set CITIZEN_UI_PORT=$Port
set CITIZEN_OPEN_BROWSER=0
set PYTHONPATH=$SeedRoot\runtime
cd /d $SeedRoot
"$py" "$living"
"@ | Set-Content -Encoding ASCII $wrapper

  $bin = "cmd.exe /c `"$wrapper`""
  sc.exe stop $ServiceName 2>$null
  sc.exe delete $ServiceName 2>$null
  sc.exe create $ServiceName binPath= $bin start= auto DisplayName= "Citizen 0.2 Living"
  sc.exe start $ServiceName
  Write-Host "Installed Windows service via sc.exe: $ServiceName"
  Write-Host "Prefer installing NSSM for better service semantics."
}

Write-Host "UI: http://${HostBind}:${Port}/"
