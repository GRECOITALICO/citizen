#Requires -Version 5.1
<#
.SYNOPSIS
  Register ONE Windows Scheduled Task to start WSL → systemd → existing Citizen unit.
#>
param(
  [string]$Distro = "CONRRAD-Citizen",
  [string]$Unit = "citizen-seed-living.service",
  [string]$TaskName = "CONRRAD-Citizen-WSL2-Autostart"
)

$ErrorActionPreference = "Stop"

$action = "wsl.exe -d `"$Distro`" --exec /bin/bash -lc `"systemctl --user start $Unit 2>/dev/null || true`""
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
  Write-Host "OK: scheduled task '$TaskName' already exists (idempotent)"
  exit 0
}

$trigger = New-ScheduledTaskTrigger -AtLogOn
$taskAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -Command `"$action`""
Register-ScheduledTask -TaskName $TaskName -Action $taskAction -Trigger $trigger -Description "Start Citizen via WSL2/systemd after Windows logon" | Out-Null
Write-Host "OK: registered '$TaskName'"
