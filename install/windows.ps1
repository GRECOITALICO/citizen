# CONRRAD Citizen — public Windows host bootstrap (WSL2).
# One instruction. Self-elevates. Resumes after reboot. Never Syncs.
#
# powershell -NoProfile -ExecutionPolicy Bypass -Command "iwr -useb https://raw.githubusercontent.com/GRECOITALICO/citizen/citizen-windows-wsl2-0.4.2.1/install/windows.ps1 | iex"
#
# Windows is Host infrastructure. WSL2 is Host infrastructure.
# The managed Linux environment is the runtime boundary.
# Citizen is the same product certified on Linux.
param()
$ErrorActionPreference = "Stop"
$PublicTag = "citizen-windows-wsl2-0.4.2.1"
$LinuxInstallTag = "citizen-managed-0.4.2.1"
$PublicOrigin = "https://raw.githubusercontent.com/GRECOITALICO/citizen/$PublicTag"
$BootstrapUrl = "$PublicOrigin/install/windows.ps1"
$GuestUrl = "$PublicOrigin/install/windows-guest.sh"
$LinuxInstallUrl = "https://raw.githubusercontent.com/GRECOITALICO/citizen/$LinuxInstallTag/install.sh"
$ImageName = "ghcr.io/grecoitalico/citizen"
$ImageDigest = "sha256:64df202d553c5aaff9cc0c74b01b8617e5877253778c9766d51dd59febd840da"
$Distro = "CONRRAD-Citizen"
$RootfsName = "ubuntu-noble-wsl-amd64-24.04lts.rootfs.tar.gz"
$RootfsUrl = "https://cloud-images.ubuntu.com/wsl/releases/24.04/current/$RootfsName"
$SumsUrl = "https://cloud-images.ubuntu.com/wsl/releases/24.04/current/SHA256SUMS"
$StateDir = Join-Path $env:LOCALAPPDATA "CONRRAD\CitizenHost"
$VolumeWin = Join-Path $env:LOCALAPPDATA "CONRRAD\Citizen"
$StateFile = Join-Path $StateDir "bootstrap.json"
$SelfPath = Join-Path $StateDir "install\windows.ps1"
$GuestPath = Join-Path $StateDir "install\windows-guest.sh"
$TaskName = "CONRRAD Citizen Host Resume"
New-Item -ItemType Directory -Force -Path (Join-Path $StateDir "install") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $StateDir "distro") | Out-Null
New-Item -ItemType Directory -Force -Path $VolumeWin | Out-Null

function Test-IsElevated {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function ConvertTo-WslPath([string]$WinPath) {
    $p = $WinPath.Replace("\", "/")
    if ($p -match "^([A-Za-z]):(.*)$") {
        return "/mnt/$($Matches[1].ToLower())$($Matches[2])"
    }
    return $p
}

function Write-HostState([string]$Phase, [bool]$Wsl2 = $false) {
    @{
        phase = $Phase
        distro = $Distro
        wsl2 = $Wsl2
        bootstrap_url = $BootstrapUrl
        image = "$ImageName@$ImageDigest"
    } | ConvertTo-Json | Set-Content -Encoding utf8 $StateFile
}

function Save-BootstrapCopy {
    New-Item -ItemType Directory -Force -Path (Split-Path $SelfPath) | Out-Null
    if ($PSCommandPath -and (Test-Path -LiteralPath $PSCommandPath)) {
        Copy-Item -LiteralPath $PSCommandPath -Destination $SelfPath -Force
    } else {
        Invoke-WebRequest -UseBasicParsing -Uri $BootstrapUrl -OutFile $SelfPath
    }
    $copiedGuest = $false
    if ($PSCommandPath -and (Test-Path -LiteralPath $PSCommandPath)) {
        $here = Split-Path -Parent $PSCommandPath
        foreach ($name in @("windows-guest.sh", "guest_bootstrap.sh")) {
            $sib = Join-Path $here $name
            if (Test-Path -LiteralPath $sib) {
                Copy-Item -LiteralPath $sib -Destination $GuestPath -Force
                $copiedGuest = $true
                break
            }
        }
    }
    if (-not $copiedGuest) {
        try {
            Invoke-WebRequest -UseBasicParsing -Uri $GuestUrl -OutFile $GuestPath
        } catch {
            if (-not (Test-Path -LiteralPath $GuestPath)) {
                throw "Could not persist the public guest bootstrap from $GuestUrl"
            }
        }
    }
}

function Register-ResumeAfterReboot {
    Save-BootstrapCopy
    $tr = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$SelfPath`""
    schtasks.exe /Create /TN $TaskName /TR $tr /SC ONLOGON /RL HIGHEST /F | Out-Null
    New-Item -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce" -Force | Out-Null
    New-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce" -Name "CONRRADCitizenHost" -Value $tr -PropertyType String -Force | Out-Null
}

function Unregister-ResumeAfterReboot {
    schtasks.exe /Delete /TN $TaskName /F 2>$null | Out-Null
}

function Request-Elevation {
    Write-HostState "wsl_enable_requested"
    Save-BootstrapCopy
    Write-Host "Requesting Administrator approval for WSL2 enablement."
    $arg = "-NoProfile -ExecutionPolicy Bypass -File `"$SelfPath`""
    $p = Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList $arg -Wait -PassThru
    if (-not $p) { exit 2 }
    exit $p.ExitCode
}

function Write-PendingReboot([string]$Message) {
    Write-HostState "wsl_pending_reboot" $false
    Register-ResumeAfterReboot
    Write-Host $Message
    Write-Host "After reboot, the same bootstrap resumes automatically. No second command. No Citizen was born."
}

function Test-LegacyVolume {
    $hints = @(
        (Join-Path $env:LOCALAPPDATA "CONRRAD\CitizenData"),
        (Join-Path $env:USERPROFILE ".conrrad\citizen"),
        (Join-Path $VolumeWin "CitizenSetup.py")
    )
    foreach ($h in $hints) {
        if (Test-Path -LiteralPath $h) { return $true }
    }
    return $false
}

function Test-KnownCitizen {
    $sealed = Join-Path $VolumeWin "identity\SEALED"
    $ident = Join-Path $VolumeWin "identity\identity.json"
    if (-not (Test-Path -LiteralPath $sealed)) { return $false }
    if (-not (Test-Path -LiteralPath $ident)) { return $false }
    $raw = Get-Content -Raw -LiteralPath $ident
    return $raw -match '"cit_'
}

Save-BootstrapCopy

if (Test-LegacyVolume) {
    Write-HostState "failed"
    Write-Host "UNKNOWN_LEGACY_INSTALLATION"
    Write-Host "An unrecognized legacy Citizen-like install was found. It was not migrated or overwritten."
    exit 3
}

$wslMissing = -not (Get-Command wsl.exe -ErrorAction SilentlyContinue)
if ($wslMissing -and -not (Test-IsElevated)) {
    Request-Elevation
}

if ($wslMissing) {
    Write-HostState "wsl_enable_requested"
    Write-Host "Enabling WSL2. UAC may already have been granted."
    wsl.exe --install --no-distribution
    Write-PendingReboot "WSL2 enablement requires a reboot."
    exit 2
}

wsl.exe --status 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    if (-not (Test-IsElevated)) { Request-Elevation }
    Write-PendingReboot "WSL2 is not operational. Reboot if Windows requires it."
    exit 2
}

Write-HostState "wsl_ready" $false

$list = (wsl.exe -l -v | Out-String)
if ($list -match [regex]::Escape($Distro) -and $list -match "$Distro\s+\S+\s+1(\s|$)") {
    Write-Host "$Distro is WSL1. Attempting in-place upgrade. Other distros are not changed."
    wsl.exe --set-version $Distro 2
}

if ($list -notmatch [regex]::Escape($Distro)) {
    Write-HostState "distro_provisioning" $false
    $dest = Join-Path $StateDir "distro"
    $rootfs = Join-Path $StateDir $RootfsName
    Write-Host "Fetching official Ubuntu SHA256SUMS."
    $sums = (Invoke-WebRequest -UseBasicParsing -Uri $SumsUrl).Content
    $expected = $null
    foreach ($line in ($sums -split "\r?\n")) {
        if ($line -match [regex]::Escape($RootfsName)) {
            $expected = ($line -split "\s+")[0].ToLower()
            break
        }
    }
    if (-not $expected) {
        Write-HostState "failed"
        Write-Host "Ubuntu SHA256SUMS did not list $RootfsName. Rootfs was not imported."
        exit 1
    }
    Write-Host "Downloading $RootfsName for $Distro."
    Invoke-WebRequest -UseBasicParsing -Uri $RootfsUrl -OutFile $rootfs
    $actual = (Get-FileHash -Algorithm SHA256 -Path $rootfs).Hash.ToLower()
    if ($actual -ne $expected) {
        Remove-Item -Force $rootfs
        Write-HostState "failed"
        Write-Host "Rootfs SHA256 mismatch vs official SHA256SUMS. File discarded. Not imported."
        exit 1
    }
    $bytes = [System.IO.File]::ReadAllBytes($rootfs)
    if ($bytes.Length -lt 2 -or $bytes[0] -ne 0x1F -or $bytes[1] -ne 0x8B) {
        Remove-Item -Force $rootfs
        Write-HostState "failed"
        Write-Host "Rootfs is not gzip tar as required by wsl --import. Not imported."
        exit 1
    }
    Write-Host "Provisioning $Distro as WSL2. Other WSL distributions are not changed."
    wsl.exe --import $Distro $dest $rootfs --version 2
}

$probe = (wsl.exe -d $Distro --exec /bin/true 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0) {
    Write-HostState "failed" $false
    Write-Host "Managed distro $Distro cannot execute commands. No Citizen was born."
    exit 1
}

Write-HostState "runtime_provisioning" $true
$volWsl = ConvertTo-WslPath $VolumeWin
Write-HostState "citizen_birth" $true
$envLine = "CITIZEN_HOME='$volWsl' CITIZEN_DATA_DIR='$volWsl' CITIZEN_LINUX_INSTALL_URL='$LinuxInstallUrl' CITIZEN_IMAGE='$ImageName@$ImageDigest' CITIZEN_OPEN_BROWSER=0"
Get-Content -Raw -LiteralPath $GuestPath | wsl.exe -d $Distro --exec /bin/bash -lc "export $envLine; /bin/bash -s"
$code = $LASTEXITCODE
if ($code -eq 0) {
    Write-HostState "ready" $true
    Unregister-ResumeAfterReboot
    Start-Process "http://127.0.0.1:3434/"
} else {
    Write-HostState "failed" $true
}
exit $code
