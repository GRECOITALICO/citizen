#Requires -Version 5.1
<#
.SYNOPSIS
  Minimal launcher: wake WSL distro, open existing Citizen UI in default browser.
  UI remains served by Linux Citizen Core on 127.0.0.1 only.
#>
param(
  [string]$Distro = "CONRRAD-Citizen",
  [string]$UiHost = "127.0.0.1",
  [int]$UiPort = 3434
)

$ErrorActionPreference = "Stop"

if ($UiHost -ne "127.0.0.1") {
  throw "Citizen UI must use localhost only (127.0.0.1)."
}

$url = "http://${UiHost}:${UiPort}/"
wsl.exe -d $Distro --exec /bin/true | Out-Null
Start-Process $url
Write-Host "OK: opened $url"
