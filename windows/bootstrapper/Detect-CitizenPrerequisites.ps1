#Requires -Version 5.1
<#
.SYNOPSIS
  Fail-closed prerequisite detection for the Citizen WSL2 bootstrapper.
  No Git, Python, cloud CLIs, or KMS credentials required.
#>
param(
  [switch]$Json
)

$ErrorActionPreference = "Stop"

function Get-PendingReboot {
  $keys = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired",
    "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\PendingFileRenameOperations"
  )
  foreach ($k in $keys) {
    if (Test-Path $k) { return $true }
  }
  return $false
}

function Get-NestedVirtHint {
  try {
    $cpu = Get-CimInstance -ClassName Win32_Processor -ErrorAction Stop | Select-Object -First 1
    return [bool]$cpu.VirtualizationFirmwareEnabled
  } catch {
    return $false
  }
}

$os = Get-CimInstance Win32_OperatingSystem
$arch = $env:PROCESSOR_ARCHITECTURE
$wslCmd = Get-Command wsl.exe -ErrorAction SilentlyContinue
$wslPresent = [bool]$wslCmd
$wslStatus = ""
$wsl2 = $false
if ($wslPresent) {
  $wslStatus = (wsl.exe --status 2>&1 | Out-String)
  $wsl2 = ($wslStatus -match "2") -and ($wslStatus -notmatch "Default Version:\s*1")
  if ($wslStatus -match "WSL1" -and $wslStatus -notmatch "WSL2") { $wsl2 = $false }
}

$vmPlatform = $false
try {
  $feat = Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -ErrorAction SilentlyContinue
  if ($feat -and $feat.State -eq "Enabled") { $vmPlatform = $true }
} catch { }

$wslFeature = $false
try {
  $feat = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -ErrorAction SilentlyContinue
  if ($feat -and $feat.State -eq "Enabled") { $wslFeature = $true }
} catch { }

$rebootPending = Get-PendingReboot
$nested = Get-NestedVirtHint
$build = [int]$os.BuildNumber
$okBuild = $build -ge 20348  # Server 2022 / Win11-class

$failClosed = @()
if (-not $okBuild) { $failClosed += "Windows build $build is too old. Windows Server 2022 or Windows 11 required." }
if ($arch -notin @("AMD64", "x86_64")) { $failClosed += "Architecture $arch is not supported. x64 required." }
if ($rebootPending) { $failClosed += "A Windows reboot is pending. Reboot, then re-run CitizenSetup." }
if (-not $wslPresent -and -not $wslFeature) { $failClosed += "WSL is not installed. The installer will enable it if you re-run after approving UAC, then reboot." }
if ($wslPresent -and -not $wsl2 -and ($wslStatus -match "WSL1")) { $failClosed += "WSL1 is the default. WSL2 is required. Nested virtualization must be enabled." }
if ($wslPresent -and -not $nested -and -not $wsl2) { $failClosed += "Nested virtualization / Virtual Machine Platform does not look available. Enable it (EC2: NestedVirtualization=enabled) and reboot." }

$report = [ordered]@{
  windows_caption     = $os.Caption
  windows_build       = $build
  architecture        = $arch
  wsl_present         = $wslPresent
  wsl_feature         = $wslFeature
  vm_platform         = $vmPlatform
  wsl2                = $wsl2
  nested_virt_hint    = $nested
  reboot_pending      = $rebootPending
  wsl_status_excerpt  = ($wslStatus.Trim() -replace "\s+", " ").Substring(0, [Math]::Min(240, ($wslStatus.Trim() -replace "\s+", " ").Length))
  fail_closed         = $failClosed
  ok                  = ($failClosed.Count -eq 0)
}

if ($Json) {
  $report | ConvertTo-Json -Compress
} else {
  Write-Host "Windows: $($report.windows_caption) build $($report.windows_build) $($report.architecture)"
  Write-Host "WSL present=$wslPresent feature=$wslFeature wsl2=$wsl2 vm_platform=$vmPlatform nested=$nested reboot_pending=$rebootPending"
  if (-not $report.ok) {
    Write-Host "FAIL-CLOSED:"
    $failClosed | ForEach-Object { Write-Host "  - $_" }
    exit 2
  }
  Write-Host "OK: prerequisites"
}
exit 0
