$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $repoRoot

Write-Host "Building CitizenSetup.exe..."
# Ensure pyinstaller is available
$pyinstallerCmd = Get-Command pyinstaller -ErrorAction SilentlyContinue
if (-not $pyinstallerCmd) {
    Write-Host "Installing PyInstaller..."
    python -m pip install pyinstaller
}

# Run PyInstaller
pyinstaller packaging\windows\CitizenSetup.spec --noconfirm --clean

if (-not $?) {
    throw "PyInstaller build failed."
}

Write-Host "Build completed successfully."
