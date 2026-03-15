Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$AppName = "ytdlp-tui"
$InstallerStateDir = Join-Path $env:LOCALAPPDATA "ytdlp-tui-installer"
$MetadataPath = Join-Path $InstallerStateDir "install.json"

function Write-Step {
    param([string]$Message)
    Write-Host "[ytdlp-tui] $Message"
}

function Load-Metadata {
    if (-not (Test-Path $MetadataPath)) {
        throw "Installation metadata was not found. Reinstall the app or remove it manually."
    }
    return Get-Content -Path $MetadataPath -Raw | ConvertFrom-Json
}

$metadata = Load-Metadata
$installDir = $metadata.install_dir
$startMenuDir = $metadata.start_menu_dir

Write-Host ""
Write-Host "This will remove:"
Write-Host "  App folder: $installDir"
Write-Host "  Start Menu folder: $startMenuDir"
Write-Host ""

$confirmation = Read-Host "Type REMOVE to continue"
if ($confirmation -ne "REMOVE") {
    Write-Step "Uninstall cancelled."
    exit 0
}

if (Test-Path $installDir) {
    Write-Step "Removing installed files..."
    Remove-Item $installDir -Recurse -Force
}

if (Test-Path $startMenuDir) {
    Write-Step "Removing Start Menu shortcuts..."
    Remove-Item $startMenuDir -Recurse -Force
}

if (Test-Path $MetadataPath) {
    Remove-Item $MetadataPath -Force
}

$installedUninstaller = Join-Path $InstallerStateDir "uninstall-ytdlp-tui.ps1"
if (Test-Path $installedUninstaller) {
    Remove-Item $installedUninstaller -Force
}

if ((Test-Path $InstallerStateDir) -and -not (Get-ChildItem $InstallerStateDir -Force | Select-Object -First 1)) {
    Remove-Item $InstallerStateDir -Force
}

Write-Step "Uninstall complete."
