# CONRRAD Citizen — public Windows host bootstrap (WSL2).
# One instruction. Self-elevates. Resumes after reboot. Never Sync.
#
# powershell -NoProfile -ExecutionPolicy Bypass -Command "iwr -useb https://raw.githubusercontent.com/GRECOITALICO/citizen/citizen-windows-wsl2-0.4.2.2/install/windows.ps1 | iex"
#
# Windows is Host infrastructure. WSL2 is Host infrastructure.
# The managed Linux environment is the runtime boundary.
# Citizen is the same product certified on Linux.
param()
$ErrorActionPreference = "Stop"
$PublicTag = "citizen-windows-wsl2-0.4.2.2"
$LinuxInstallTag = "citizen-managed-0.4.2.1"
$PublicOrigin = "https://raw.githubusercontent.com/GRECOITALICO/citizen/$PublicTag"
$BootstrapUrl = "$PublicOrigin/install/windows.ps1"
$GuestUrl = "$PublicOrigin/install/windows-guest.sh"
$LinuxInstallUrl = "https://raw.githubusercontent.com/GRECOITALICO/citizen/$LinuxInstallTag/install.sh"
$ImageName = "ghcr.io/grecoitalico/citizen"
$ImageDigest = "sha256:64df202d553c5aaff9cc0c74b01b8617e5877253778c9766d51dd59febd840da"
$Distro = "CONRRAD-Citizen"
$RootfsName = "ubuntu-noble-wsl-amd64-24.04lts.rootfs.tar.gz"
$StateDir = Join-Path $env:LOCALAPPDATA "CONRRAD\CitizenHost"
$VolumeWin = Join-Path $env:LOCALAPPDATA "CONRRAD\Citizen"
$StateFile = Join-Path $StateDir "bootstrap.json"
$SelfPath = Join-Path $StateDir "install\windows.ps1"
$GuestPath = Join-Path $StateDir "install\windows-guest.sh"
$TaskName = "CONRRAD Citizen Host Resume"
$script:DiagPhase = "start"
$script:DiagShaUrl = ""
$script:DiagShaStatus = ""
$script:DiagShaFinalUrl = ""
$script:DiagShaContentType = ""
$script:DiagShaContentLength = ""
$script:DiagChecksumFound = $false
$script:DiagExpected = ""
$script:DiagActual = ""
New-Item -ItemType Directory -Force -Path (Join-Path $StateDir "install") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $StateDir "distro") | Out-Null
New-Item -ItemType Directory -Force -Path $VolumeWin | Out-Null

function Write-CitizenHost([string]$Msg) {
    Write-Host "[Citizen Host] $Msg"
}

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
    $script:DiagPhase = $Phase
    @{
        phase = $Phase
        BOOTSTRAP_PHASE = $Phase
        distro = $Distro
        wsl2 = $Wsl2
        bootstrap_url = $BootstrapUrl
        image = "$ImageName@$ImageDigest"
        SHA_URL = $script:DiagShaUrl
        SHA_HTTP_STATUS = $script:DiagShaStatus
        SHA_FINAL_URL = $script:DiagShaFinalUrl
        SHA_CONTENT_TYPE = $script:DiagShaContentType
        SHA_CONTENT_LENGTH = $script:DiagShaContentLength
        ROOTFS_NAME = $RootfsName
        CHECKSUM_SOURCE_FOUND = $script:DiagChecksumFound
        EXPECTED_SHA256 = $script:DiagExpected
        ACTUAL_SHA256 = $script:DiagActual
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
    $arg = "-NoProfile -ExecutionPolicy Bypass -File `"$SelfPath`""
    $p = Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList $arg -Wait -PassThru
    if (-not $p) { exit 2 }
    exit $p.ExitCode
}

function Write-PendingReboot {
    Write-HostState "wsl_pending_reboot" $false
    Register-ResumeAfterReboot
    Write-Host "Reboot required. Citizen has not been created yet."
    Write-Host "The installation will resume automatically after Windows starts."
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

function Test-UnknownVolumeContent {
    if (Test-KnownCitizen) { return $false }
    if (-not (Test-Path -LiteralPath $VolumeWin)) { return $false }
    $kids = @(Get-ChildItem -Force -LiteralPath $VolumeWin -ErrorAction SilentlyContinue)
    return $kids.Count -gt 0
}

function Test-PortOccupied {
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $iar = $client.BeginConnect("127.0.0.1", 3434, $null, $null)
        $wait = $iar.AsyncWaitHandle.WaitOne(300, $false)
        $open = $false
        if ($wait) {
            try {
                $client.EndConnect($iar)
                $open = $client.Connected
            } catch {
                $open = $false
            }
        }
        $client.Close()
        return $open
    } catch {
        return $false
    }
}

function ConvertFrom-ChecksumBytes([byte[]]$Bytes) {
    if ($null -eq $Bytes -or $Bytes.Length -eq 0) { return "" }
    $utf16 = $false
    if ($Bytes.Length -ge 2 -and $Bytes[0] -eq 0xFF -and $Bytes[1] -eq 0xFE) { $utf16 = $true }
    elseif ($Bytes.Length -ge 2 -and $Bytes[0] -eq 0xFE -and $Bytes[1] -eq 0xFF) { $utf16 = $true }
    elseif ($Bytes.Length -ge 8) {
        $nuls = 0
        $lim = [Math]::Min($Bytes.Length, 400)
        for ($i = 1; $i -lt $lim; $i += 2) {
            if ($Bytes[$i] -eq 0) { $nuls++ }
        }
        if ($nuls -ge [int]($lim / 4)) { $utf16 = $true }
    }
    if ($utf16) {
        $text = [Text.Encoding]::Unicode.GetString($Bytes)
    } else {
        $text = [Text.Encoding]::UTF8.GetString($Bytes)
    }
    return (($text -replace "`0", "").TrimStart([char]0xFEFF))
}

function Test-ChecksumManifestBad([string]$Text, [string]$ContentType) {
    $ctype = ""
    if ($ContentType) { $ctype = (($ContentType -split ";")[0]).Trim().ToLower() }
    if ($ctype -and @("text/plain", "application/octet-stream", "binary/octet-stream") -notcontains $ctype) {
        return "unexpected_mime"
    }
    if ([string]::IsNullOrWhiteSpace($Text)) { return "empty" }
    $take = [Math]::Min(2048, $Text.Length)
    $head = $Text.Substring(0, $take).ToLower()
    if ($head.StartsWith("<!doctype html") -or $head.StartsWith("<html") -or $head.Contains("<html")) {
        return "html"
    }
    if ($head.Contains("<form") -and ($head.Contains("login") -or $head.Contains("password") -or $head.Contains("sign in"))) {
        return "login_page"
    }
    if ($head.Contains("proxy") -and ($head.Contains("error") -or $head.Contains("<"))) {
        return "proxy_error"
    }
    return $null
}

function Get-RootfsChecksumFromManifest([string]$Text, [string]$FileName) {
    foreach ($line in ($Text -split "\r?\n")) {
        $line = $line.Trim()
        if (-not $line -or $line.StartsWith("#")) { continue }
        $parts = $line -split "\s+"
        if ($parts.Count -lt 2) { continue }
        $digest = $parts[0].ToLower()
        if ($digest -notmatch '^[0-9a-f]{64}$') { continue }
        $name = $parts[-1].TrimStart("*")
        if ($name -eq $FileName -or $name.EndsWith("/$FileName")) { return $digest }
    }
    return $null
}

function Get-OfficialHttpFile([string]$Uri, [string]$OutFile) {
    $meta = @{
        Url = $Uri
        Status = 0
        FinalUrl = $Uri
        ContentType = ""
        ContentLength = 0
        Body = [byte[]]@()
        Error = ""
    }
    try {
        $resp = Invoke-WebRequest -UseBasicParsing -Uri $Uri -OutFile $OutFile -PassThru
        $meta.Status = [int]$resp.StatusCode
        $ct = $resp.Headers["Content-Type"]
        if ($ct -is [array]) { $meta.ContentType = [string]$ct[0] } else { $meta.ContentType = [string]$ct }
        if ($resp.BaseResponse -and $resp.BaseResponse.ResponseUri) {
            $meta.FinalUrl = [string]$resp.BaseResponse.ResponseUri
        }
        if (Test-Path -LiteralPath $OutFile) {
            $meta.Body = [IO.File]::ReadAllBytes($OutFile)
            $meta.ContentLength = $meta.Body.Length
        }
    } catch {
        $meta.Error = [string]$_.Exception.Message
        try {
            if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
                $meta.Status = [int]$_.Exception.Response.StatusCode
            }
        } catch { }
    }
    return $meta
}

function Show-RootfsVerifyFailed([string]$Reason) {
    Write-HostState "failed"
    Write-Host "Ubuntu rootfs verification could not be completed."
    Write-Host "No WSL distro was imported and no Citizen was created."
    if ($Reason) {
        Write-Host $Reason
    }
}

function Resolve-OfficialRootfs {
    $sources = @(
        @{
            Sums = "https://cloud-images.ubuntu.com/wsl/releases/24.04/current/SHA256SUMS"
            Rootfs = "https://cloud-images.ubuntu.com/wsl/releases/24.04/current/$RootfsName"
        },
        @{
            Sums = "https://cloud-images.ubuntu.com/wsl/releases/noble/current/SHA256SUMS"
            Rootfs = "https://cloud-images.ubuntu.com/wsl/releases/noble/current/$RootfsName"
        }
    )
    $lastReason = "Official Ubuntu checksum data was not usable."
    foreach ($src in $sources) {
        $sumsDir = $src.Sums.Substring(0, $src.Sums.LastIndexOf("/") + 1)
        $paired = $sumsDir + $RootfsName
        if ($src.Rootfs -ne $paired) {
            $script:DiagShaUrl = $src.Sums
            Show-RootfsVerifyFailed "Checksum source and rootfs filename do not correspond. No WSL distro was imported."
            return $null
        }
        $probePath = Join-Path $StateDir "SHA256SUMS.probe"
        $meta = Get-OfficialHttpFile $src.Sums $probePath
        $script:DiagShaUrl = $src.Sums
        $script:DiagShaStatus = [string]$meta.Status
        $script:DiagShaFinalUrl = $meta.FinalUrl
        $script:DiagShaContentType = $meta.ContentType
        $script:DiagShaContentLength = [string]$meta.ContentLength
        $script:DiagChecksumFound = $false
        $script:DiagExpected = ""
        Write-HostState "distro_provisioning" $false
        $text = ConvertFrom-ChecksumBytes $meta.Body
        $bad = Test-ChecksumManifestBad $text $meta.ContentType
        if ($bad) {
            $lastReason = "Official checksum manifest was HTML, empty, a login/proxy page, or an unexpected type."
            continue
        }
        $expected = Get-RootfsChecksumFromManifest $text $RootfsName
        if (-not $expected) {
            $lastReason = "Official checksum manifest did not list $RootfsName as a SHA256 line."
            continue
        }
        $script:DiagChecksumFound = $true
        $script:DiagExpected = $expected
        Write-HostState "distro_provisioning" $false
        return @{ Expected = $expected; RootfsUrl = $src.Rootfs; SumsUrl = $src.Sums }
    }
    Show-RootfsVerifyFailed $lastReason
    return $null
}

Save-BootstrapCopy
Write-CitizenHost "Verifying Windows..."

if (Test-LegacyVolume -or Test-UnknownVolumeContent) {
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
    Write-CitizenHost "Provisioning WSL2..."
    wsl.exe --install --no-distribution
    Write-PendingReboot
    exit 2
}

wsl.exe --status 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    if (-not (Test-IsElevated)) { Request-Elevation }
    Write-PendingReboot
    exit 2
}

Write-HostState "wsl_ready" $false

if (Test-KnownCitizen) {
    Write-CitizenHost "Existing Citizen detected. Resuming."
}

if ((Test-PortOccupied) -and -not (Test-KnownCitizen)) {
    Write-HostState "failed" $false
    Write-Host "Port 127.0.0.1:3434 is occupied by an unknown process."
    Write-Host "The occupying process was not stopped."
    Write-Host "No second Citizen was created."
    exit 4
}

$list = (wsl.exe -l -v | Out-String)
if ($list -match [regex]::Escape($Distro) -and $list -match "$Distro\s+\S+\s+1(\s|$)") {
    Write-CitizenHost "Provisioning WSL2..."
    wsl.exe --set-version $Distro 2
}

if ($list -notmatch [regex]::Escape($Distro)) {
    Write-HostState "distro_provisioning" $false
    $dest = Join-Path $StateDir "distro"
    $rootfs = Join-Path $StateDir $RootfsName
    Write-CitizenHost "Verifying Ubuntu rootfs metadata..."
    $resolved = Resolve-OfficialRootfs
    if (-not $resolved) { exit 1 }
    Write-CitizenHost "Downloading rootfs..."
    Invoke-WebRequest -UseBasicParsing -Uri $resolved.RootfsUrl -OutFile $rootfs
    $actual = (Get-FileHash -Algorithm SHA256 -Path $rootfs).Hash.ToLower()
    $script:DiagActual = $actual
    Write-HostState "distro_provisioning" $false
    if ($actual -ne $resolved.Expected) {
        Remove-Item -Force $rootfs
        Write-HostState "failed"
        Write-Host "Rootfs SHA256 mismatch vs official SHA256SUMS. File discarded. Not imported."
        Write-Host "No WSL distro was imported and no Citizen was created."
        exit 1
    }
    $bytes = [System.IO.File]::ReadAllBytes($rootfs)
    if ($bytes.Length -lt 2 -or $bytes[0] -ne 0x1F -or $bytes[1] -ne 0x8B) {
        Remove-Item -Force $rootfs
        Write-HostState "failed"
        Write-Host "Rootfs is not gzip tar as required by wsl --import. Not imported."
        Write-Host "No WSL distro was imported and no Citizen was created."
        exit 1
    }
    Write-CitizenHost "SHA256 verified..."
    Write-CitizenHost "Provisioning WSL2..."
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
Write-CitizenHost "Provisioning Citizen environment..."
if (-not (Test-KnownCitizen)) {
    Write-HostState "citizen_birth" $true
}
$envLine = "CITIZEN_HOME='$volWsl' CITIZEN_DATA_DIR='$volWsl' CITIZEN_LINUX_INSTALL_URL='$LinuxInstallUrl' CITIZEN_IMAGE='$ImageName@$ImageDigest' CITIZEN_OPEN_BROWSER=0"
Get-Content -Raw -LiteralPath $GuestPath | wsl.exe -d $Distro --exec /bin/bash -lc "export $envLine; /bin/bash -s"
$code = $LASTEXITCODE
if ($code -eq 0) {
    Write-HostState "ready" $true
    Unregister-ResumeAfterReboot
    Write-CitizenHost "Citizen READY."
    Start-Process "http://127.0.0.1:3434/"
} else {
    Write-HostState "failed" $true
}
exit $code
