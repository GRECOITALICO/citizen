# CONRRAD Citizen — public Windows host bootstrap (WSL2).
# One instruction. Self-elevates. Resumes after reboot. Recovers the existing Citizen.
# Installs the host-owned Runtime Evolution Seed. Never Sync. Never Births twice.
#
# powershell -NoProfile -ExecutionPolicy Bypass -Command "iwr -useb https://raw.githubusercontent.com/GRECOITALICO/citizen/citizen-windows-wsl2-0.4.2.8/install/windows.ps1 | iex"
#
# Windows is Host infrastructure. WSL2 is Host infrastructure.
# The managed Linux environment is the runtime boundary.
# Citizen is the same product certified on Linux.
param()
$ErrorActionPreference = "Stop"
$PublicTag = "citizen-windows-wsl2-0.4.2.8"
$LinuxInstallTag = "citizen-managed-0.4.2.1"
$InstallerVersion = "0.4.2.8"
$HostSeedVersion = "0.4.2.8"
$PublicOrigin = "https://raw.githubusercontent.com/GRECOITALICO/citizen/$PublicTag"
$BootstrapUrl = "$PublicOrigin/install/windows.ps1"
$GuestUrl = "$PublicOrigin/install/windows-guest.sh"
$RequirementsUrl = "$PublicOrigin/install/windows/requirements.json"
$HostSeedUrl = "$PublicOrigin/install/windows/host-seed/run.py"
$HostSeedWheelUrl = "$PublicOrigin/install/windows/host-seed/conrrad_citizen-0.4.2.2-py3-none-any.whl"
$ClassPackageUrl = "$PublicOrigin/install/windows/CLASS_PACKAGE.json"
$LinuxInstallUrl = "https://raw.githubusercontent.com/GRECOITALICO/citizen/$LinuxInstallTag/install.sh"
$ImageName = "ghcr.io/grecoitalico/citizen"
$ImageDigest = "sha256:446da11ded1a23a64d1c906b98383215606d257a598026e99cc8b8cdeea0635e"
$SourceImageDigest = "sha256:64df202d553c5aaff9cc0c74b01b8617e5877253778c9766d51dd59febd840da"
$Distro = "CONRRAD-Citizen"
$RootfsName = "ubuntu-noble-wsl-amd64-24.04lts.rootfs.tar.gz"
$StateDir = Join-Path $env:LOCALAPPDATA "CONRRAD\CitizenHost"
$VolumeWin = Join-Path $env:LOCALAPPDATA "CONRRAD\Citizen"
$StateFile = Join-Path $StateDir "bootstrap.json"
$SelfPath = Join-Path $StateDir "install\windows.ps1"
$GuestPath = Join-Path $StateDir "install\windows-guest.sh"
$RequirementsPath = Join-Path $StateDir "install\requirements.json"
$HostSeedDir = Join-Path $StateDir "host-seed"
$HostSeedRun = Join-Path $HostSeedDir "run.py"
$HostSeedWheel = Join-Path $HostSeedDir "conrrad_citizen-0.4.2.2-py3-none-any.whl"
$ClassPackagePath = Join-Path $HostSeedDir "CLASS_PACKAGE.json"
$TaskName = "CONRRAD Citizen Host Resume"
$script:BootstrapPhase = "BOOTSTRAP_STARTED"
$script:PlanId = ""
$script:ResumeMarker = $false
$script:AuthorizationGranted = $false
$script:RequirementsState = @{}
$script:DiagPhase = "start"
$script:DiagShaUrl = ""
$script:DiagShaStatus = ""
$script:DiagShaFinalUrl = ""
$script:DiagShaContentType = ""
$script:DiagShaContentLength = ""
$script:DiagChecksumFound = $false
$script:DiagExpected = ""
$script:DiagActual = ""
$script:WslProbe = ""
$script:WslProbeExitCode = ""
$script:WslProbeStderrClass = ""
$script:WslExecution = ""
$script:SystemdUserSession = ""
$script:FilesystemProbe = ""
$script:BashProbe = ""
$script:ContainerEngineProbe = ""
$script:NetworkProbe = ""
$script:ManagedUserProbe = ""
$script:SystemdProductRequirement = "FALSE"
$script:InstallClass = ""
$script:ManagedDistroClass = ""
$script:ManagedDistroRegistered = $false
$script:PriorBootstrapOurs = $false
$script:PriorPhase = ""
$script:RebootResume = $false
$script:ResumeTaskState = ""
$script:ProductReady = "FALSE"
$script:BootstrapResult = ""
$script:InstallationResult = ""
$script:ReadinessResult = ""
$script:BirthMode = ""
$script:ObservedCitizen = ""
$script:LivingVersion = ""
$script:UiPort = "3434"
$script:HttpStatus = ""
$script:CleanupWarnings = @()
$script:CleanupClass = "INFORMATIONAL"
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

function Get-LegacyPhaseAlias([string]$Phase) {
    switch ($Phase) {
        "AUTHORIZATION_REQUIRED" { return "wsl_enable_requested" }
        "PROVISIONING" { return "wsl_enable_requested" }
        "REBOOT_REQUIRED" { return "wsl_pending_reboot" }
        "RESUMING" { return "wsl_ready" }
        "ENVIRONMENT_READY" { return "runtime_provisioning" }
        "PROVISIONING_WSL" { return "wsl_enable_requested" }
        "VERIFYING_WSL" { return "wsl_ready" }
        "PROVISIONING_CONTAINER_ENGINE" { return "runtime_provisioning" }
        "VERIFYING_CONTAINER_ENGINE" { return "runtime_provisioning" }
        "VERIFYING_PUBLIC_IMAGE" { return "runtime_provisioning" }
        "CREATING_ENVIRONMENT" { return "runtime_provisioning" }
        "HOST_SEED" { return "runtime_provisioning" }
        "BIRTH_OR_RESUME" { return "runtime_provisioning" }
        "RUNTIME_EVOLUTION" { return "runtime_provisioning" }
        "VERIFYING_CITIZEN" { return "runtime_provisioning" }
        "POST_START_HOUSEKEEPING" { return "ready" }
        "READY" { return "ready" }
        "CITIZEN_READY" { return "ready" }
        "COMPLETE" { return "ready" }
        "UNKNOWN_LEGACY" { return "failed" }
        "PORT_CONFLICT" { return "failed" }
        "UNSUPPORTED_HOST" { return "failed" }
        "USER_DECLINED" { return "failed" }
        "PROVISION_FAILED" { return "failed" }
        "VERIFICATION_FAILED" { return "failed" }
        "REBOOT_RESUME_FAILED" { return "failed" }
        default { return $Phase }
    }
}

function Write-HostState {
    param(
        [string]$Phase,
        [bool]$Wsl2 = $false
    )
    $script:BootstrapPhase = $Phase
    $script:DiagPhase = $Phase
    $script:ResumeMarker = @(
        "AUTHORIZATION_REQUIRED", "PROVISIONING", "PROVISIONING_WSL", "REBOOT_REQUIRED", "RESUMING"
    ) -contains $Phase
    # Canonical persisted field is bootstrap_phase only.
    # FAILURE_CLASS=PUBLIC_BOOTSTRAP_PARSE_ERROR AFFECTED_VERSION=0.4.2.3
    # ROOT_CAUSE=CASE_INSENSITIVE_DUPLICATE_HASH_KEY
    # Windows PowerShell rejected Write-HostState before execution:
    # DuplicateKeyInHashLiteral — "No se permiten claves duplicadas 'BOOTSTRAP_PHASE' en los literales de hash."
    # Do not add BOOTSTRAP_PHASE as a second key; hash keys are case-insensitive.
    $payload = [ordered]@{
        bootstrap_phase = $Phase
        phase = (Get-LegacyPhaseAlias $Phase)
        plan_id = $script:PlanId
        resume_marker = $script:ResumeMarker
        installer_version = $InstallerVersion
        timestamp = [DateTime]::UtcNow.ToString("o")
        authorization_granted = [bool]$script:AuthorizationGranted
        requirements_state = $script:RequirementsState
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
        WSL_PROBE = $script:WslProbe
        WSL_PROBE_EXIT_CODE = $script:WslProbeExitCode
        WSL_PROBE_STDERR_CLASS = $script:WslProbeStderrClass
        WSL_EXECUTION = $script:WslExecution
        SYSTEMD_USER_SESSION = $script:SystemdUserSession
        FILESYSTEM_PROBE = $script:FilesystemProbe
        BASH_PROBE = $script:BashProbe
        CONTAINER_ENGINE_PROBE = $script:ContainerEngineProbe
        NETWORK_PROBE = $script:NetworkProbe
        MANAGED_USER_PROBE = $script:ManagedUserProbe
        SYSTEMD_PRODUCT_REQUIREMENT = $script:SystemdProductRequirement
        install_class = $script:InstallClass
        managed_distro_class = $script:ManagedDistroClass
        managed_distro_registered = [bool]$script:ManagedDistroRegistered
        resume_task_state = $script:ResumeTaskState
        PRODUCT_READY = $script:ProductReady
        BOOTSTRAP_RESULT = $script:BootstrapResult
        INSTALLATION_RESULT = $script:InstallationResult
        READINESS_RESULT = $script:ReadinessResult
        BIRTH_MODE = $script:BirthMode
        CITIZEN_ID = $script:ObservedCitizen
        LIVING_VERSION = $script:LivingVersion
        PORT = $script:UiPort
        HTTP_STATUS = $script:HttpStatus
        HOST_SEED_VERSION = $HostSeedVersion
        HOST_SEED_INSTALLED = [bool](Test-Path -LiteralPath (Join-Path $HostSeedDir "VERSION"))
        SOURCE_IMAGE = "$ImageName@$SourceImageDigest"
        CLEANUP_WARNINGS = @($script:CleanupWarnings)
        CLEANUP_CLASS = $script:CleanupClass
    }
    $payload | ConvertTo-Json -Compress | Set-Content -Encoding utf8 $StateFile
}

function Read-HostState {
    if (-not (Test-Path -LiteralPath $StateFile)) { return $null }
    try {
        return (Get-Content -Raw -LiteralPath $StateFile | ConvertFrom-Json)
    } catch {
        return $null
    }
}

function Get-CanonicalBootstrapPhase($st) {
    if ($null -eq $st) { return "" }
    foreach ($n in @($st.PSObject.Properties.Name)) {
        if ($n -ieq "bootstrap_phase") { return [string]$st.$n }
    }
    foreach ($n in @($st.PSObject.Properties.Name)) {
        if ($n -ieq "phase") { return [string]$st.$n }
    }
    return ""
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
    $copiedReq = $false
    if ($PSCommandPath -and (Test-Path -LiteralPath $PSCommandPath)) {
        $here = Split-Path -Parent $PSCommandPath
        $sib = Join-Path $here "requirements.json"
        if (Test-Path -LiteralPath $sib) {
            Copy-Item -LiteralPath $sib -Destination $RequirementsPath -Force
            $copiedReq = $true
        }
    }
    if (-not $copiedReq) {
        try {
            Invoke-WebRequest -UseBasicParsing -Uri $RequirementsUrl -OutFile $RequirementsPath
        } catch {
            if (-not (Test-Path -LiteralPath $RequirementsPath)) {
                throw "Could not persist the Windows requirements manifest from $RequirementsUrl"
            }
        }
    }
    $copiedSeed = $false
    if ($PSCommandPath -and (Test-Path -LiteralPath $PSCommandPath)) {
        $here = Split-Path -Parent $PSCommandPath
        foreach ($rel in @("host-seed\run.py", "windows\host-seed\run.py")) {
            $sib = Join-Path $here $rel
            if (Test-Path -LiteralPath $sib) {
                New-Item -ItemType Directory -Force -Path $HostSeedDir | Out-Null
                Copy-Item -LiteralPath $sib -Destination $HostSeedRun -Force
                $copiedSeed = $true
                break
            }
        }
        foreach ($rel in @("CLASS_PACKAGE.json", "windows\CLASS_PACKAGE.json", "host-seed\CLASS_PACKAGE.json")) {
            $sib = Join-Path $here $rel
            if (Test-Path -LiteralPath $sib) {
                New-Item -ItemType Directory -Force -Path $HostSeedDir | Out-Null
                Copy-Item -LiteralPath $sib -Destination $ClassPackagePath -Force
                break
            }
        }
    }
    if (-not $copiedSeed) {
        try {
            New-Item -ItemType Directory -Force -Path $HostSeedDir | Out-Null
            Invoke-WebRequest -UseBasicParsing -Uri $HostSeedUrl -OutFile $HostSeedRun
        } catch {
        }
    }
    if (-not (Test-Path -LiteralPath $ClassPackagePath)) {
        try {
            New-Item -ItemType Directory -Force -Path $HostSeedDir | Out-Null
            Invoke-WebRequest -UseBasicParsing -Uri $ClassPackageUrl -OutFile $ClassPackagePath
        } catch {
        }
    }
    if (-not (Test-Path -LiteralPath $HostSeedWheel)) {
        $copiedWheel = $false
        if ($PSCommandPath -and (Test-Path -LiteralPath $PSCommandPath)) {
            $here = Split-Path -Parent $PSCommandPath
            foreach ($rel in @("host-seed\conrrad_citizen-0.4.2.2-py3-none-any.whl", "windows\host-seed\conrrad_citizen-0.4.2.2-py3-none-any.whl")) {
                $sib = Join-Path $here $rel
                if (Test-Path -LiteralPath $sib) {
                    New-Item -ItemType Directory -Force -Path $HostSeedDir | Out-Null
                    Copy-Item -LiteralPath $sib -Destination $HostSeedWheel -Force
                    $copiedWheel = $true
                    break
                }
            }
        }
        if (-not $copiedWheel) {
            try {
                New-Item -ItemType Directory -Force -Path $HostSeedDir | Out-Null
                Invoke-WebRequest -UseBasicParsing -Uri $HostSeedWheelUrl -OutFile $HostSeedWheel
            } catch {
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

function Get-ResumeTaskState {
    if (Get-Command Get-ScheduledTask -ErrorAction SilentlyContinue) {
        try {
            $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
            if ($t) {
                if ([string]$t.State -eq "Running") { return "RUNNING" }
                return "EXISTS"
            }
        } catch {
        }
    }
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $PSNativeCommandUseErrorActionPreference = $false
    $raw = schtasks.exe /Query /TN $TaskName 2>&1
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    $blob = (($raw | Out-String) + "")
    if ($code -eq 0) { return "EXISTS" }
    if ($blob -match "cannot find the file specified" -or $blob -match "No se puede encontrar el archivo especificado" -or $blob -match "cannot find the path specified" -or $blob -match "does not exist") {
        return "MISSING"
    }
    if ($code -ne 0) { return "MISSING" }
    return "MISSING"
}

function Unregister-ResumeAfterReboot {
    # Cleanup is never allowed to turn a successful installation into failure.
    # ERROR_TASK_NOT_FOUND / "The system cannot find the file specified." = TASK_ALREADY_ABSENT.
    $state = Get-ResumeTaskState
    $script:ResumeTaskState = $state
    if ($state -eq "MISSING" -or $state -eq "NOT_REQUIRED") {
        $script:ResumeTaskState = "TASK_ALREADY_ABSENT"
    } else {
        $prev = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        $PSNativeCommandUseErrorActionPreference = $false
        $raw = schtasks.exe /Delete /TN $TaskName /F 2>&1
        $code = $LASTEXITCODE
        $ErrorActionPreference = $prev
        $blob = (($raw | Out-String) + "")
        if ($code -eq 0) {
            $script:ResumeTaskState = "TASK_REMOVED"
        } elseif ($blob -match "cannot find the file specified" -or $blob -match "No se puede encontrar el archivo especificado" -or $blob -match "cannot find the path specified" -or $blob -match "does not exist") {
            $script:ResumeTaskState = "TASK_ALREADY_ABSENT"
        } else {
            $script:ResumeTaskState = "TASK_DELETE_FAILED"
        }
    }
    try {
        $runOnce = "HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce"
        if (Test-Path -LiteralPath $runOnce) {
            Remove-ItemProperty -Path $runOnce -Name "CONRRADCitizenHost" -ErrorAction SilentlyContinue
        }
    } catch {
    }
}

function Request-Elevation {
    Write-HostState "AUTHORIZATION_REQUIRED"
    Save-BootstrapCopy
    $arg = "-NoProfile -ExecutionPolicy Bypass -File `"$SelfPath`""
    try {
        $p = Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList $arg -Wait -PassThru
    } catch {
        Write-Fail "USER_DECLINED" "Windows permission was not granted." "Citizen did not enable Windows features.`nCitizen did not create a Citizen.`nCitizen did not modify your existing WSL distributions." $false
        exit 2
    }
    if (-not $p) {
        Write-Fail "USER_DECLINED" "Windows permission was not granted." "Citizen did not enable Windows features.`nCitizen did not create a Citizen.`nCitizen did not modify your existing WSL distributions." $false
        exit 2
    }
    exit $p.ExitCode
}

function Write-PendingReboot {
    Write-HostState "REBOOT_REQUIRED" $false
    Register-ResumeAfterReboot
    Write-Host "Reboot required. Citizen has not been created yet."
    Write-Host "The installation will resume automatically after Windows starts."
}

function Write-Fail([string]$Phase, [string]$What, [string]$DidNot, [bool]$ActionRequired) {
    Write-HostState $Phase $false
    Write-Host $What
    if ($DidNot) { Write-Host $DidNot }
    if ($ActionRequired) {
        Write-Host "USER_ACTION_REQUIRED"
    } else {
        Write-Host "No additional command is required right now."
    }
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

function Get-VolumeClass {
    if (Test-LegacyVolume -and -not $script:PriorBootstrapOurs) { return "UNKNOWN_LEGACY_RESOURCE" }
    if (Test-KnownCitizen) { return "KNOWN_MANAGED_CITIZEN" }
    if (Test-UnknownVolumeContent -and -not $script:PriorBootstrapOurs) { return "UNKNOWN_LEGACY_RESOURCE" }
    if ($script:PriorBootstrapOurs) { return "MANAGED_INSTALL_IN_PROGRESS" }
    return "NO_CITIZEN"
}

function Get-InstallClass {
    if (Test-KnownCitizen) { return "MANAGED_INSTALL_READY" }
    $vol = Get-VolumeClass
    if ($vol -eq "UNKNOWN_LEGACY_RESOURCE") { return "UNKNOWN_LEGACY_INSTALLATION" }
    if ($script:ManagedDistroClass -eq "UNKNOWN_DISTRO") { return "UNKNOWN_DISTRO" }
    if ($vol -eq "KNOWN_MANAGED_CITIZEN") { return "MANAGED_INSTALL_READY" }
    if ($script:PriorBootstrapOurs -or $vol -eq "MANAGED_INSTALL_IN_PROGRESS") {
        return "MANAGED_INSTALL_IN_PROGRESS"
    }
    return "NO_INSTALLATION"
}

function Test-HostBootstrapOurs($st) {
    if ($null -eq $st) { return $false }
    if ($st.managed_distro_registered -eq $true) { return $true }
    if ([string]$st.distro -eq $Distro) { return $true }
    $url = [string]$st.bootstrap_url
    if ($url -match "citizen-windows-wsl2") { return $true }
    return $false
}

function Test-DestVhdxPresent {
    $dest = Join-Path $StateDir "distro"
    if (-not (Test-Path -LiteralPath $dest)) { return $false }
    $hits = @(Get-ChildItem -Force -LiteralPath $dest -Filter "*.vhdx" -ErrorAction SilentlyContinue)
    return ($hits.Count -gt 0)
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

function Get-PortClass {
    $occupied = Test-PortOccupied
    if (-not $occupied) { return "FREE" }
    if (Test-KnownCitizen) { return "CURRENT_CITIZEN" }
    try {
        $probe = Read-CitizenProductReadiness
        if ($probe.Ready) { return "CURRENT_CITIZEN" }
    } catch {
    }
    return "UNKNOWN_PROCESS"
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
    Write-Fail "VERIFICATION_FAILED" "Ubuntu verification could not be completed." ("Citizen did not import WSL.`nCitizen did not create a Citizen.`nCitizen did not modify your existing WSL distributions.`n" + $(if ($Reason) { $Reason } else { "Ubuntu rootfs verification could not be completed." }) + "`nNo WSL distro was imported and no Citizen was created.") $false
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
        Write-HostState "PROVISIONING" $false
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
        Write-HostState "PROVISIONING" $false
        return @{ Expected = $expected; RootfsUrl = $src.Rootfs; SumsUrl = $src.Sums }
    }
    Show-RootfsVerifyFailed $lastReason
    return $null
}

function Get-RequirementsManifest {
    if (-not (Test-Path -LiteralPath $RequirementsPath)) {
        Save-BootstrapCopy
    }
    $raw = Get-Content -Raw -LiteralPath $RequirementsPath
    return ($raw | ConvertFrom-Json)
}

function Test-WslPresent {
    return [bool](Get-Command wsl.exe -ErrorAction SilentlyContinue)
}

function Test-WslOperational {
    if (-not (Test-WslPresent)) { return $false }
    wsl.exe --status 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Get-ManagedDistroList {
    if (-not (Test-WslPresent)) { return "" }
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $PSNativeCommandUseErrorActionPreference = $false
    $raw = ((wsl.exe -l -v | Out-String) + "")
    $ErrorActionPreference = $prev
    return ($raw -replace "`0", "")
}

function Test-ManagedDistroPresent {
    $list = Get-ManagedDistroList
    return [bool]($list -match [regex]::Escape($Distro))
}

function Test-GuestManagedMarker {
    $r = Invoke-WslExec @("-d", $Distro, "--exec", "/bin/bash", "-lc", "if test -f /etc/conrrad-citizen-managed || grep -q CONRRAD-managed /etc/wsl.conf 2>/dev/null; then printf MARKER_OK; else printf MARKER_MISSING; fi")
    return [bool]($r.Stdout -match "MARKER_OK")
}

function Get-DistroOwnership {
    if (-not (Test-ManagedDistroPresent)) { return "ABSENT" }
    if ($script:PriorBootstrapOurs -or $script:ManagedDistroRegistered -or (Test-DestVhdxPresent)) {
        return "KNOWN_MANAGED_DISTRO"
    }
    $marker = $false
    try {
        $marker = Test-GuestManagedMarker
    } catch {
        $marker = $false
    }
    if ($marker) { return "KNOWN_MANAGED_DISTRO" }
    return "UNKNOWN_DISTRO"
}

function Write-UnknownDistroFail {
    Write-Fail "PROVISION_FAILED" "Citizen found a WSL distribution named CONRRAD-Citizen that it does not own." "Citizen did not create a Citizen.`nCitizen did not modify unrelated WSL distributions.`nCitizen did not unregister the existing distribution." $false
}

function Write-UnrecoverableDistroFail {
    $script:InstallClass = "MANAGED_INSTALL_BROKEN"
    Write-Fail "PROVISION_FAILED" "Citizen found an existing managed Linux environment that could not be recovered automatically." "Citizen did not create a Citizen.`nCitizen did not modify unrelated WSL distributions.`nCitizen did not unregister the existing distribution." $false
}

function Get-CitizenHttp {
    param([string]$Path)
    $url = "http://127.0.0.1:$($script:UiPort)$Path"
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $resp = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 3
        return [pscustomobject]@{ Status = [int]$resp.StatusCode; Body = [string]$resp.Content }
    } catch {
        $code = 0
        try {
            if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
                $code = [int]$_.Exception.Response.StatusCode
            }
        } catch {
        }
        return [pscustomobject]@{ Status = $code; Body = "" }
    } finally {
        $ErrorActionPreference = $prev
    }
}

function Read-CitizenProductReadiness {
    $lifeHit = Get-CitizenHttp "/api/life"
    $livingHit = Get-CitizenHttp "/api/living"
    $rootHit = Get-CitizenHttp "/"
    $status = 0
    if ($lifeHit.Status -eq 200) { $status = 200 }
    elseif ($livingHit.Status -eq 200) { $status = 200 }
    elseif ($rootHit.Status -eq 200) { $status = 200 }
    $script:HttpStatus = [string]$status
    $life = $null
    $living = $null
    try { if ($lifeHit.Body) { $life = $lifeHit.Body | ConvertFrom-Json } } catch { }
    try { if ($livingHit.Body) { $living = $livingHit.Body | ConvertFrom-Json } } catch { }
    $state = ""
    $cid = ""
    $ver = ""
    if ($life -and $life.citizen) {
        $state = [string]$life.citizen.state
        $cid = [string]$life.citizen.citizen_id
        $ver = [string]$life.citizen.version
    }
    if ($living) {
        if (-not $cid) { $cid = [string]$living.citizen_id }
        if (-not $ver) { $ver = [string]$living.citizen_seed_version }
        if (-not $state) {
            if ([string]$living.alive_status -eq "Alive" -and [string]$living.identity_status -eq "sealed" -and $cid -like "cit_*") {
                $state = "READY"
            }
        }
    }
    $httpOk = ($status -eq 200)
    $stateReady = ($state -eq "READY")
    $ready = ($httpOk -and $stateReady)
    if ($cid) { $script:ObservedCitizen = $cid }
    if ($ver) { $script:LivingVersion = $ver }
    if ($ready) {
        $script:ProductReady = "TRUE"
        $script:ReadinessResult = "READY"
    } else {
        $script:ProductReady = "FALSE"
        $script:ReadinessResult = "NOT_READY"
    }
    return [pscustomobject]@{
        Ready = $ready
        HttpOk = $httpOk
        StateReady = $stateReady
        Status = $status
        State = $state
        Citizen = $cid
        Version = $ver
    }
}

function Wait-CitizenProductReady {
    param(
        [int]$Attempts = 30,
        [int]$DelaySec = 2
    )
    $last = $null
    for ($i = 0; $i -lt $Attempts; $i++) {
        $last = Read-CitizenProductReadiness
        if ($last.Ready) { return $last }
        if ($i -lt ($Attempts - 1)) { Start-Sleep -Seconds $DelaySec }
    }
    return $last
}

function Invoke-PostStartHousekeeping {
    Write-HostState "POST_START_HOUSEKEEPING" $true
    $script:CleanupClass = "INFORMATIONAL"
    $script:CleanupWarnings = @()
    try {
        Unregister-ResumeAfterReboot
        if ($script:ResumeTaskState -eq "TASK_DELETE_FAILED") {
            $script:CleanupClass = "WARNING"
            $script:CleanupWarnings += "scheduled task cleanup failed"
        }
    } catch {
        $script:CleanupClass = "WARNING"
        $script:CleanupWarnings += "cleanup exception"
        $script:ResumeTaskState = "TASK_DELETE_FAILED"
    }
}

function Complete-BootstrapSuccess {
    $script:InstallationResult = "SUCCESS"
    $script:BootstrapResult = "SUCCESS"
    $script:ProductReady = "TRUE"
    $script:ReadinessResult = "READY"
    $script:InstallClass = "MANAGED_INSTALL_READY"
    Write-HostState "CITIZEN_READY" $true
    Write-HostState "READY" $true
    Invoke-PostStartHousekeeping
    Write-HostState "COMPLETE" $true
    Write-CitizenHost "Citizen is READY."
    Write-CitizenHost "Installation complete."
    if ($script:CleanupClass -eq "WARNING") {
        Write-CitizenHost "Cleanup warning recorded; Citizen remains healthy."
    }
    Write-Host "http://127.0.0.1:$($script:UiPort)/"
    try { Start-Process "http://127.0.0.1:$($script:UiPort)/" } catch { }
    exit 0
}

function Install-HostSeed {
    Write-HostState "HOST_SEED" $true
    Write-CitizenHost "Updating host runtime seed."
    New-Item -ItemType Directory -Force -Path $HostSeedDir | Out-Null
    Set-Content -Encoding ascii -Path (Join-Path $HostSeedDir "VERSION") -Value $HostSeedVersion
    Save-BootstrapCopy
    $receipt = Join-Path $StateDir "HOST_SEED_RECEIPTS.jsonl"
    $row = '{"kind":"HOST_SEED_STARTED","owner":"HOST_ADAPTER","version":"' + $HostSeedVersion + '"}'
    Add-Content -Encoding utf8 -Path $receipt -Value $row
}

function Invoke-StartExistingEnvironment {
    $cmd = "if command -v podman >/dev/null 2>&1; then podman start conrrad-citizen >/dev/null 2>&1 || true; printf STARTED; else printf NO_ENGINE; fi"
    $r = Invoke-WslExec @("-d", $Distro, "-u", "citizen", "--exec", "/bin/bash", "-lc", $cmd)
    return [bool]($r.Stdout -match "STARTED")
}

function Invoke-HostSeedEvolution {
    Write-HostState "RUNTIME_EVOLUTION" $true
    Write-CitizenHost "Ready for runtime evolution."
    $volWsl = ConvertTo-WslPath $VolumeWin
    $hostWsl = ConvertTo-WslPath $StateDir
    $pkgWsl = ConvertTo-WslPath $ClassPackagePath
    if (-not (Test-Path -LiteralPath $ClassPackagePath)) {
        return $true
    }
    $wheelWsl = "$hostWsl/host-seed/conrrad_citizen-0.4.2.2-py3-none-any.whl"
    $libWsl = "$hostWsl/host-seed/lib"
    $prep = "export DEBIAN_FRONTEND=noninteractive; apt-get update -y >/dev/null 2>&1; apt-get install -y --no-install-recommends python3 python3-cryptography >/dev/null 2>&1; python3 -c 'import os,sys,zipfile; os.makedirs(sys.argv[2], exist_ok=True); zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])' '$wheelWsl' '$libWsl'"
    Invoke-WslExec @("-d", $Distro, "-u", "root", "--exec", "/bin/bash", "-lc", $prep) | Out-Null
    $py = "PYTHONPATH='$libWsl' python3 -m conrrad_citizen.host.seed_cli --home '$volWsl' --data-dir '$hostWsl' --envelope '$pkgWsl'"
    $r = Invoke-WslExec @("-d", $Distro, "-u", "citizen", "--exec", "/bin/bash", "-lc", $py)
    Set-WslProbeMeta "host_seed" $r
    if ($r.Stdout -match '"ok": true' -or $r.Stdout -match '"ok":true') { return $true }
    if ($r.ExitCode -eq 0) { return $true }
    return $false
}

function Invoke-ExistingCitizenRecovery {
    Write-CitizenHost "Existing Citizen detected."
    Write-CitizenHost "Preserving Citizen volume."
    Install-HostSeed
    Write-CitizenHost "Verifying managed environment."
    $before = Read-CitizenProductReadiness
    if (-not $before.Ready) {
        Invoke-StartExistingEnvironment | Out-Null
        $null = Wait-CitizenProductReady -Attempts 20 -DelaySec 2
    }
    Invoke-HostSeedEvolution | Out-Null
    $after = Wait-CitizenProductReady -Attempts 30 -DelaySec 2
    if ($after.Ready) {
        if ($before.Ready) {
            $script:BirthMode = "ALREADY_RUNNING"
        } else {
            $script:BirthMode = "RESUME"
        }
        Complete-BootstrapSuccess
    }
    $script:InstallationResult = "FAILURE"
    $script:BootstrapResult = "FAILURE"
    Write-Fail "PROVISION_FAILED" "Existing Citizen was preserved but could not be started." "Citizen did not create a second Citizen.`nCitizen did not unregister the existing distribution.`nNo additional command is required right now." $false
    exit 1
}

function Classify-WslStderr([string]$Stderr) {
    if ([string]::IsNullOrWhiteSpace($Stderr)) { return "" }
    if ($Stderr -match "CreateProcess|0xc0000142|WSL_E_") { return "CREATE_PROCESS_FAILURE" }
    if ($Stderr -match "Exec format error|cannot execute") { return "BIN_EXEC_FAILURE" }
    if ($Stderr -match "Read-only file system|No space left on device") { return "FILESYSTEM_FAILURE" }
    if ($Stderr -match "Failed to start the systemd user session") { return "SYSTEMD_USER_SESSION_WARNING" }
    if ($Stderr -match "No such file or directory") { return "BIN_EXEC_FAILURE" }
    return "UNKNOWN"
}

function Set-WslProbeMeta([string]$Name, $Result) {
    $script:WslProbe = $Name
    $script:WslProbeExitCode = [string]$Result.ExitCode
    $script:WslProbeStderrClass = Classify-WslStderr $Result.Stderr
    if ($script:WslProbeStderrClass -eq "SYSTEMD_USER_SESSION_WARNING") {
        $script:SystemdUserSession = "DEGRADED"
    }
}

function Invoke-WslExec {
    param([Parameter(Mandatory = $true)][string[]]$WslArgs)
    $PSNativeCommandUseErrorActionPreference = $false
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $stdoutParts = New-Object System.Collections.Generic.List[string]
    $stderrParts = New-Object System.Collections.Generic.List[string]
    $code = 1
    try {
        $raw = & wsl.exe @WslArgs 2>&1
        $code = $LASTEXITCODE
        if ($null -eq $code) { $code = 0 }
        foreach ($item in @($raw)) {
            if ($null -eq $item) { continue }
            if ($item -is [System.Management.Automation.ErrorRecord]) {
                $msg = [string]$item
                if ($item.Exception -and $item.Exception.Message) {
                    $msg = [string]$item.Exception.Message
                }
                [void]$stderrParts.Add($msg)
            } else {
                $s = [string]$item
                if ($s -match '(?i)^wsl:\s' -or $s -match "Failed to start the systemd user session") {
                    [void]$stderrParts.Add($s)
                } else {
                    [void]$stdoutParts.Add($s)
                }
            }
        }
    } catch {
        if ($LASTEXITCODE) { $code = [int]$LASTEXITCODE } else { $code = 1 }
        [void]$stderrParts.Add([string]$_)
    } finally {
        $ErrorActionPreference = $prev
    }
    return [pscustomobject]@{
        ExitCode = [int]$code
        Stdout = ($stdoutParts -join "`n")
        Stderr = ($stderrParts -join "`n")
    }
}

function Test-WslBinTrueFatal($Result) {
    $cls = Classify-WslStderr $Result.Stderr
    if ($cls -eq "CREATE_PROCESS_FAILURE") { return $true }
    if ($cls -eq "BIN_EXEC_FAILURE") { return $true }
    if ($cls -eq "FILESYSTEM_FAILURE") { return $true }
    return $false
}

function Write-ManagedEnvironmentFail {
    Write-Fail "PROVISION_FAILED" "Citizen could not start its managed Linux environment." "Citizen did not create a Citizen.`nCitizen did not modify unrelated WSL distributions." $false
}

function Ensure-ManagedLinuxUser {
    $cmd = "if ! id -u citizen >/dev/null 2>&1; then useradd -m -s /bin/bash citizen; fi; grep -q '^citizen:' /etc/subuid 2>/dev/null || echo 'citizen:100000:65536' >> /etc/subuid; grep -q '^citizen:' /etc/subgid 2>/dev/null || echo 'citizen:100000:65536' >> /etc/subgid; if id -u citizen >/dev/null 2>&1; then printf USER_OK; else printf USER_FAIL; fi"
    $r = Invoke-WslExec @("-d", $Distro, "-u", "root", "--exec", "/bin/bash", "-lc", $cmd)
    Set-WslProbeMeta "ensure_managed_user" $r
    return ($r.Stdout -match "USER_OK")
}

function Test-ManagedEnvironmentPostGuest {
    $engine = Invoke-WslExec @("-d", $Distro, "--exec", "/bin/bash", "-lc", "if command -v podman >/dev/null 2>&1; then printf ENGINE_OK; else printf ENGINE_FAIL; fi")
    Set-WslProbeMeta "container_engine" $engine
    if ($engine.Stdout -notmatch "ENGINE_OK") {
        $script:ContainerEngineProbe = "FAIL"
        return $false
    }
    $script:ContainerEngineProbe = "PASS"
    $user = Invoke-WslExec @("-d", $Distro, "--exec", "/bin/bash", "-lc", "if id -u citizen >/dev/null 2>&1; then printf USER_OK; else printf USER_MISSING; fi")
    Set-WslProbeMeta "managed_user" $user
    if ($user.Stdout -notmatch "USER_OK") {
        $script:ManagedUserProbe = "FAIL"
        return $false
    }
    $script:ManagedUserProbe = "PASS"
    $rootless = Invoke-WslExec @("-d", $Distro, "--exec", "/bin/bash", "-lc", "if grep -q '^citizen:' /etc/subuid; then printf ROOTLESS_OK; else printf ROOTLESS_FAIL; fi")
    Set-WslProbeMeta "rootless" $rootless
    if ($rootless.Stdout -notmatch "ROOTLESS_OK") {
        $script:ContainerEngineProbe = "FAIL"
        return $false
    }
    return $true
}

function Test-ManagedDistroOperational {
    # Capability probes. WSL systemd user-session health is not Citizen health.
    # SYSTEMD_PRODUCT_REQUIREMENT=FALSE — do not disable systemd blindly.
    $script:SystemdProductRequirement = "FALSE"
    $trueProbe = Invoke-WslExec @("-d", $Distro, "--exec", "/bin/true")
    Set-WslProbeMeta "bin_true" $trueProbe
    if (Test-WslBinTrueFatal $trueProbe) {
        $script:WslExecution = "UNAVAILABLE"
        return $false
    }
    $bash = Invoke-WslExec @("-d", $Distro, "--exec", "/bin/bash", "-lc", "printf READY")
    Set-WslProbeMeta "bash_ready" $bash
    if ($bash.Stdout -notmatch "READY") {
        $script:WslExecution = "UNAVAILABLE"
        $script:BashProbe = "FAIL"
        return $false
    }
    $script:BashProbe = "PASS"
    $script:WslExecution = "AVAILABLE"
    if (-not $script:SystemdUserSession) { $script:SystemdUserSession = "OK" }
    $bashx = Invoke-WslExec @("-d", $Distro, "--exec", "/bin/bash", "-lc", "if test -x /bin/bash; then printf BASH_OK; else printf BASH_FAIL; fi")
    Set-WslProbeMeta "bash_exec" $bashx
    if ($bashx.Stdout -notmatch "BASH_OK") {
        $script:BashProbe = "FAIL"
        $script:WslExecution = "UNAVAILABLE"
        return $false
    }
    $idProbe = Invoke-WslExec @("-d", $Distro, "--exec", "/bin/bash", "-lc", "id")
    Set-WslProbeMeta "id" $idProbe
    if ($idProbe.Stdout -notmatch "uid=") {
        $script:WslExecution = "UNAVAILABLE"
        return $false
    }
    $fs = Invoke-WslExec @("-d", $Distro, "--exec", "/bin/bash", "-lc", "if test -w /tmp; then printf FS_OK; else printf FS_FAIL; fi")
    Set-WslProbeMeta "filesystem" $fs
    if ($fs.Stdout -notmatch "FS_OK") {
        $script:FilesystemProbe = "FAIL"
        return $false
    }
    $script:FilesystemProbe = "PASS"
    $user = Invoke-WslExec @("-d", $Distro, "--exec", "/bin/bash", "-lc", "if id -u citizen >/dev/null 2>&1; then printf USER_OK; else printf USER_MISSING; fi")
    Set-WslProbeMeta "managed_user" $user
    if ($user.Stdout -match "USER_OK") {
        $script:ManagedUserProbe = "PASS"
    } else {
        $script:ManagedUserProbe = "MISSING"
        if (-not (Ensure-ManagedLinuxUser)) { return $false }
        $script:ManagedUserProbe = "PASS"
    }
    $engine = Invoke-WslExec @("-d", $Distro, "--exec", "/bin/bash", "-lc", "if command -v podman >/dev/null 2>&1; then printf ENGINE_OK; else printf ENGINE_FAIL; fi")
    Set-WslProbeMeta "container_engine" $engine
    if ($engine.Stdout -match "ENGINE_OK") {
        $script:ContainerEngineProbe = "PASS"
    } else {
        $script:ContainerEngineProbe = "PENDING"
    }
    $net = Invoke-WslExec @("-d", $Distro, "--exec", "/bin/bash", "-lc", "if getent ahosts ghcr.io >/dev/null 2>&1 || getent hosts ghcr.io >/dev/null 2>&1 || (test -r /etc/resolv.conf && grep -q nameserver /etc/resolv.conf); then printf NET_OK; else printf NET_FAIL; fi")
    Set-WslProbeMeta "network" $net
    if ($net.Stdout -notmatch "NET_OK") {
        $script:NetworkProbe = "FAIL"
        return $false
    }
    $script:NetworkProbe = "PASS"
    return $true
}

function Show-AuthorizationScreen {
    Write-CitizenHost "Windows needs permission to continue."
    Write-Host ""
    Write-Host "Citizen needs permission to prepare Windows."
    Write-Host "The following system components may be enabled:"
    Write-Host "  * WSL2"
    Write-Host "  * Virtual Machine Platform"
    Write-Host "  * required managed-environment infrastructure"
    Write-Host ""
    Write-Host "[ Continue ]"
    try {
        $null = Read-Host "Press Enter to continue"
    } catch {
        Write-Fail "USER_DECLINED" "Windows permission was not granted." "Citizen did not enable Windows features.`nCitizen did not create a Citizen." $false
        exit 2
    }
    $script:AuthorizationGranted = $true
    Write-HostState "AUTHORIZATION_REQUIRED"
    Write-CitizenHost "Permission granted."
}

function Set-RequirementStatus([string]$Id, [string]$Status) {
    $script:RequirementsState[$Id] = $Status
}

function Invoke-RequirementDetect($Item) {
    $id = [string]$Item.id
    switch ($id) {
        "windows_version" {
            $v = [Environment]::OSVersion.Version
            if ($v.Major -gt 10 -or ($v.Major -eq 10 -and $v.Build -ge 19041)) { return "VERIFIED" }
            return "MISSING"
        }
        "windows_architecture" {
            if ($env:PROCESSOR_ARCHITECTURE -in @("AMD64", "X64")) { return "VERIFIED" }
            return "MISSING"
        }
        "powershell" {
            if ($PSVersionTable.PSVersion.Major -gt 5 -or ($PSVersionTable.PSVersion.Major -eq 5 -and $PSVersionTable.PSVersion.Minor -ge 1)) {
                return "VERIFIED"
            }
            return "MISSING"
        }
        "administrator_elevation" {
            if (Test-IsElevated) { return "VERIFIED" }
            if (Test-WslOperational) { return "PRESENT" }
            return "MISSING"
        }
        "virtualization" {
            try {
                $cs = Get-CimInstance Win32_Processor -ErrorAction Stop | Select-Object -First 1
                if ($cs.VirtualizationFirmwareEnabled -eq $true) { return "VERIFIED" }
            } catch { }
            try {
                $h = Get-CimInstance Win32_ComputerSystem -ErrorAction Stop
                if ($h.HypervisorPresent) { return "VERIFIED" }
            } catch { }
            if (Test-WslOperational) { return "VERIFIED" }
            return "UNKNOWN"
        }
        "wsl_feature" {
            if (Test-WslOperational -or Test-WslPresent) { return "VERIFIED" }
            return "MISSING"
        }
        "virtual_machine_platform" {
            if (Test-WslOperational) { return "VERIFIED" }
            return "MISSING"
        }
        "wsl_runtime" {
            if (Test-WslOperational) { return "VERIFIED" }
            return "MISSING"
        }
        "wsl_version" {
            if (-not (Test-WslOperational)) { return "MISSING" }
            $st = (wsl.exe --status 2>$null | Out-String)
            if ($st -match "Default Version:\s*2") { return "VERIFIED" }
            $list = Get-ManagedDistroList
            if ($list -match [regex]::Escape($Distro) -and $list -match "$Distro\s+\S+\s+2(\s|$)") { return "VERIFIED" }
            return "MISSING"
        }
        "managed_distribution" {
            $list = Get-ManagedDistroList
            if ($list -match [regex]::Escape($Distro)) { return "VERIFIED" }
            return "MISSING"
        }
        "managed_distribution_version" {
            $list = Get-ManagedDistroList
            if ($list -match [regex]::Escape($Distro) -and $list -match "$Distro\s+\S+\s+2(\s|$)") { return "VERIFIED" }
            if ($list -match [regex]::Escape($Distro)) { return "MISSING" }
            return "MISSING"
        }
        "linux_user" {
            if (-not (Test-WslOperational)) { return "MISSING" }
            $list = Get-ManagedDistroList
            if ($list -notmatch [regex]::Escape($Distro)) { return "MISSING" }
            $r = Invoke-WslExec @("-d", $Distro, "--exec", "/bin/bash", "-lc", "if id -u citizen >/dev/null 2>&1; then printf USER_OK; else printf USER_MISSING; fi")
            if ($r.Stdout -match "USER_OK") { return "VERIFIED" }
            return "MISSING"
        }
        "linux_network" {
            if (-not (Test-WslOperational)) { return "MISSING" }
            $list = Get-ManagedDistroList
            if ($list -notmatch [regex]::Escape($Distro)) { return "MISSING" }
            return "PRESENT"
        }
        "linux_dns" {
            if (-not (Test-WslOperational)) { return "MISSING" }
            $list = Get-ManagedDistroList
            if ($list -notmatch [regex]::Escape($Distro)) { return "MISSING" }
            return "PRESENT"
        }
        "linux_https" {
            if (-not (Test-WslOperational)) { return "MISSING" }
            $list = Get-ManagedDistroList
            if ($list -notmatch [regex]::Escape($Distro)) { return "MISSING" }
            return "PRESENT"
        }
        "container_engine" {
            if (-not (Test-WslOperational)) { return "MISSING" }
            $list = Get-ManagedDistroList
            if ($list -notmatch [regex]::Escape($Distro)) { return "MISSING" }
            $r = Invoke-WslExec @("-d", $Distro, "--exec", "/bin/bash", "-lc", "if command -v podman >/dev/null 2>&1; then printf ENGINE_OK; else printf ENGINE_FAIL; fi")
            if ($r.Stdout -match "ENGINE_OK") { return "VERIFIED" }
            return "MISSING"
        }
        "rootless_prerequisites" {
            if (-not (Test-WslOperational)) { return "MISSING" }
            $list = Get-ManagedDistroList
            if ($list -notmatch [regex]::Escape($Distro)) { return "MISSING" }
            $r = Invoke-WslExec @("-d", $Distro, "--exec", "/bin/bash", "-lc", "if grep -q '^citizen:' /etc/subuid; then printf ROOTLESS_OK; else printf ROOTLESS_FAIL; fi")
            if ($r.Stdout -match "ROOTLESS_OK") { return "VERIFIED" }
            return "MISSING"
        }
        "public_ghcr_access" {
            try {
                Invoke-WebRequest -UseBasicParsing -Uri "https://ghcr.io/v2/" -TimeoutSec 20 | Out-Null
                return "VERIFIED"
            } catch {
                return "MISSING"
            }
        }
        "public_ubuntu_access" {
            try {
                Invoke-WebRequest -UseBasicParsing -Uri "https://cloud-images.ubuntu.com/wsl/releases/24.04/current/SHA256SUMS" -TimeoutSec 20 | Out-Null
                return "VERIFIED"
            } catch {
                return "MISSING"
            }
        }
        "disk_space" {
            $root = [string]$env:LOCALAPPDATA.Substring(0, 1)
            $drive = Get-PSDrive -Name $root -ErrorAction SilentlyContinue
            if ($drive -and $drive.Free -ge 10737418240) { return "VERIFIED" }
            return "MISSING"
        }
        "memory" {
            try {
                $m = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory
                if ($m -ge 4294967296) { return "VERIFIED" }
            } catch { }
            return "UNKNOWN"
        }
        "port_3434" {
            $cls = Get-PortClass
            if ($cls -eq "UNKNOWN_PROCESS") { return "BLOCKED" }
            return "VERIFIED"
        }
        "persistent_storage" {
            $cls = Get-VolumeClass
            if ($cls -eq "UNKNOWN_LEGACY_RESOURCE") { return "BLOCKED" }
            return "VERIFIED"
        }
        "scheduled_resume" {
            if (Test-WslOperational) { return "PRESENT" }
            return "MISSING"
        }
        default { return "UNKNOWN" }
    }
}

function Show-Inventory($Manifest) {
    Write-CitizenHost "Checking your Windows environment..."
    $labels = [ordered]@{}
    foreach ($item in $Manifest.requirements) {
        $status = Invoke-RequirementDetect $item
        Set-RequirementStatus $item.id $status
        $label = [string]$item.user_label
        if (-not $label) { $label = [string]$item.name }
        $show = "OK"
        if ($status -in @("MISSING", "BLOCKED", "UNKNOWN")) { $show = "MISSING" }
        if (-not $labels.Contains($label) -or $labels[$label] -ne "MISSING") {
            $labels[$label] = $show
        }
    }
    foreach ($key in $labels.Keys) {
        $pad = "." * [Math]::Max(2, 40 - $key.Length)
        Write-Host ("{0}{1} {2}" -f $key, $pad, $labels[$key])
    }
}

function Test-RequirementNeedsAdmin($Manifest) {
    foreach ($item in $Manifest.requirements) {
        $st = $script:RequirementsState[$item.id]
        if ($item.requires_admin -and $st -eq "MISSING") { return $true }
    }
    return $false
}

function Invoke-Provisioner([string]$Name) {
    switch ($Name) {
        "none" { return }
        "self_elevate" { return }
        "register_resume" {
            Register-ResumeAfterReboot
        }
        "wsl_install" {
            Write-CitizenHost "Preparing WSL2..."
            Write-HostState "PROVISIONING" $false
            wsl.exe --install --no-distribution
            Write-PendingReboot
            exit 2
        }
        "set_wsl_default_v2" {
            Write-CitizenHost "Preparing WSL2..."
            wsl.exe --set-default-version 2 2>$null | Out-Null
        }
        "upgrade_managed_distro_v2" {
            Write-CitizenHost "Preparing WSL2..."
            wsl.exe --set-version $Distro 2
        }
        "ensure_volume" {
            New-Item -ItemType Directory -Force -Path $VolumeWin | Out-Null
        }
        "import_managed_distro" {
            Import-ManagedDistro
        }
        "guest_prepare" {
            return
        }
        default { return }
    }
}

function Import-ManagedDistro {
    if (Test-ManagedDistroPresent) {
        Write-CitizenHost "Managed WSL distribution already exists..."
        Write-CitizenHost "Verifying existing environment..."
        $script:ManagedDistroRegistered = $true
        $script:ManagedDistroClass = "KNOWN_MANAGED_DISTRO"
        return
    }
    Write-CitizenHost "Preparing managed Citizen environment..."
    Write-HostState "PROVISIONING_WSL" $false
    $dest = Join-Path $StateDir "distro"
    $rootfs = Join-Path $StateDir $RootfsName
    Write-CitizenHost "Verifying Ubuntu rootfs metadata..."
    $resolved = Resolve-OfficialRootfs
    if (-not $resolved) { exit 1 }
    Write-CitizenHost "Downloading rootfs..."
    Invoke-WebRequest -UseBasicParsing -Uri $resolved.RootfsUrl -OutFile $rootfs
    $actual = (Get-FileHash -Algorithm SHA256 -Path $rootfs).Hash.ToLower()
    $script:DiagActual = $actual
    Write-HostState "PROVISIONING_WSL" $false
    if ($actual -ne $resolved.Expected) {
        Remove-Item -Force $rootfs
        Write-Fail "VERIFICATION_FAILED" "Ubuntu verification could not be completed." "Citizen did not import WSL.`nCitizen did not create a Citizen.`nCitizen did not modify your existing WSL distributions.`nRootfs SHA256 mismatch vs official SHA256SUMS. File discarded. Not imported.`nNo WSL distro was imported and no Citizen was created." $false
        exit 1
    }
    $bytes = [System.IO.File]::ReadAllBytes($rootfs)
    if ($bytes.Length -lt 2 -or $bytes[0] -ne 0x1F -or $bytes[1] -ne 0x8B) {
        Remove-Item -Force $rootfs
        Write-Fail "VERIFICATION_FAILED" "Ubuntu verification could not be completed." "Citizen did not import WSL.`nCitizen did not create a Citizen.`nCitizen did not modify your existing WSL distributions.`nRootfs is not gzip tar as required by wsl --import. Not imported.`nNo WSL distro was imported and no Citizen was created." $false
        exit 1
    }
    Write-CitizenHost "SHA256 verified..."
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $PSNativeCommandUseErrorActionPreference = $false
    $importOut = & wsl.exe --import $Distro $dest $rootfs --version 2 2>&1
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    $blob = (($importOut | Out-String) + "")
    if ($blob -match "ERROR_ALREADY_EXISTS") {
        Write-CitizenHost "Managed WSL distribution already exists..."
        Write-CitizenHost "Verifying existing environment..."
        $script:ManagedDistroRegistered = $true
        $script:ManagedDistroClass = "KNOWN_MANAGED_DISTRO"
        return
    }
    if ($code -ne 0) {
        Write-Fail "PROVISION_FAILED" "Citizen could not import its managed Linux environment." "Citizen did not create a Citizen.`nCitizen did not modify unrelated WSL distributions." $false
        exit 1
    }
    $script:ManagedDistroRegistered = $true
    $script:ManagedDistroClass = "KNOWN_MANAGED_DISTRO"
}

Save-BootstrapCopy
$prior = Read-HostState
if ($prior) {
    if ($prior.authorization_granted) { $script:AuthorizationGranted = $true }
    if ($prior.plan_id) { $script:PlanId = [string]$prior.plan_id }
    if ($prior.resume_marker -eq $true) { $script:ResumeMarker = $true }
    if ($prior.managed_distro_registered -eq $true) { $script:ManagedDistroRegistered = $true }
    $script:PriorPhase = Get-CanonicalBootstrapPhase $prior
    $script:PriorBootstrapOurs = Test-HostBootstrapOurs $prior
    if ($script:PriorPhase -eq "REBOOT_REQUIRED" -or $prior.phase -eq "wsl_pending_reboot") {
        $script:RebootResume = $true
        Write-HostState "RESUMING" $false
        Write-CitizenHost "Checking your Windows environment..."
    }
}
Write-HostState "BOOTSTRAP_STARTED"
Write-HostState "PREFLIGHT"

$script:InstallClass = Get-InstallClass
if ($script:InstallClass -eq "UNKNOWN_LEGACY_INSTALLATION") {
    Write-Fail "UNKNOWN_LEGACY" "UNKNOWN_LEGACY_INSTALLATION" "An unrecognized legacy Citizen-like install was found. It was not migrated or overwritten.`nCitizen did not create a Citizen.`nCitizen did not modify your existing WSL distributions." $true
    exit 3
}

$portClass = Get-PortClass
if ($portClass -eq "UNKNOWN_PROCESS") {
    Write-Fail "PORT_CONFLICT" "Port 127.0.0.1:3434 is occupied by an unknown process." "The occupying process was not stopped.`nNo second Citizen was created." $true
    exit 4
}

$manifest = Get-RequirementsManifest
Write-HostState "REQUIREMENTS_INVENTORY"
Show-Inventory $manifest
Write-HostState "PLAN"

$needsAdmin = Test-RequirementNeedsAdmin $manifest
if ($needsAdmin -and -not (Test-IsElevated)) {
    Write-HostState "AUTHORIZATION_REQUIRED"
    if (-not $script:AuthorizationGranted) {
        Show-AuthorizationScreen
    }
    Request-Elevation
}

if (-not (Test-WslOperational)) {
    Write-CitizenHost "Preparing required components..."
    Invoke-Provisioner "wsl_install"
}

wsl.exe --status 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    if (-not (Test-IsElevated)) {
        Write-HostState "AUTHORIZATION_REQUIRED"
        if (-not $script:AuthorizationGranted) { Show-AuthorizationScreen }
        Request-Elevation
    }
    Write-PendingReboot
    exit 2
}

Write-HostState "VERIFYING" $false
Invoke-Provisioner "set_wsl_default_v2"

if (Test-KnownCitizen) {
    Write-CitizenHost "Starting Citizen..."
}

Write-HostState "PROVISIONING_WSL" $false
$own = Get-DistroOwnership
$script:ManagedDistroClass = $own
if ($own -eq "UNKNOWN_DISTRO") {
    Write-UnknownDistroFail
    exit 1
}

$list = Get-ManagedDistroList
if ($own -eq "KNOWN_MANAGED_DISTRO" -and $list -match "$Distro\s+\S+\s+1(\s|$)") {
    Invoke-Provisioner "upgrade_managed_distro_v2"
}

if ($own -eq "ABSENT") {
    Invoke-Provisioner "import_managed_distro"
} else {
    Write-CitizenHost "Managed WSL distribution already exists..."
    Write-CitizenHost "Verifying existing environment..."
    $script:ManagedDistroRegistered = $true
}

Write-HostState "VERIFYING_WSL" $true
if (-not (Test-ManagedDistroOperational)) {
    if ($own -eq "KNOWN_MANAGED_DISTRO" -or $script:ManagedDistroRegistered) {
        Write-UnrecoverableDistroFail
        exit 1
    }
    Write-ManagedEnvironmentFail
    exit 1
}
$script:InstallClass = Get-InstallClass
if (Test-KnownCitizen) {
    $script:InstallClass = "MANAGED_INSTALL_READY"
} elseif ($script:PriorBootstrapOurs -or $script:ManagedDistroRegistered) {
    $script:InstallClass = "MANAGED_INSTALL_IN_PROGRESS"
}

Write-HostState "PROVISIONING_CONTAINER_ENGINE" $true
Write-HostState "VERIFYING_CONTAINER_ENGINE" $true
Write-HostState "ENVIRONMENT_READY" $true
$volWsl = ConvertTo-WslPath $VolumeWin
Install-HostSeed
if (Test-KnownCitizen) {
    Invoke-ExistingCitizenRecovery
}
if ($own -eq "KNOWN_MANAGED_DISTRO") {
    Write-CitizenHost "Existing managed environment found."
    Write-CitizenHost "Verifying environment..."
} else {
    Write-CitizenHost "Preparing managed Citizen environment..."
    Write-CitizenHost "Verifying public Citizen image..."
}
Write-HostState "VERIFYING_PUBLIC_IMAGE" $true
Write-HostState "CREATING_ENVIRONMENT" $true
Write-HostState "BIRTH_OR_RESUME" $true
Write-HostState "VERIFYING_CITIZEN" $true
$beforeFresh = Read-CitizenProductReadiness
if ($beforeFresh.Ready) {
    $script:BirthMode = "ALREADY_RUNNING"
    Complete-BootstrapSuccess
}
if (Test-KnownCitizen) {
    $script:BirthMode = "RESUME"
} else {
    $script:BirthMode = "BIRTH"
}
Write-CitizenHost "Starting Citizen..."
$envLine = "CITIZEN_HOME='$volWsl' CITIZEN_DATA_DIR='$volWsl' CITIZEN_LINUX_INSTALL_URL='$LinuxInstallUrl' CITIZEN_IMAGE='$ImageName@$ImageDigest' CITIZEN_OPEN_BROWSER=0"
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$guestOut = Get-Content -Raw -LiteralPath $GuestPath | & wsl.exe -d $Distro --exec /bin/bash -lc "export $envLine; /bin/bash -s" 2>&1
$code = $LASTEXITCODE
$ErrorActionPreference = $prevEap
$guestBlob = ($guestOut | Out-String)
Set-WslProbeMeta "guest_bootstrap" ([pscustomobject]@{ ExitCode = $code; Stdout = $guestBlob; Stderr = $guestBlob })
Install-HostSeed
Invoke-HostSeedEvolution | Out-Null
$after = Wait-CitizenProductReady -Attempts 30 -DelaySec 2
if ($after.Ready) {
    Complete-BootstrapSuccess
}
$script:InstallationResult = "FAILURE"
$script:BootstrapResult = "FAILURE"
$script:ProductReady = "FALSE"
if (-not $script:ReadinessResult) { $script:ReadinessResult = "NOT_READY" }
Write-Fail "PROVISION_FAILED" "Citizen could not be started." "Citizen did not complete Birth or Resume.`nNo additional command is required right now." $false
exit 1
