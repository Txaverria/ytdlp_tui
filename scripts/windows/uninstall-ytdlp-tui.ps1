Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$AppName = "ytdlp-tui"
$InstallerStateDir = Join-Path $env:LOCALAPPDATA "ytdlp-tui-installer"
$MetadataPath = Join-Path $InstallerStateDir "install.json"

function Write-Step {
    param([string]$Message)
    Write-Host "[ytdlp-tui] $Message"
}

function Assert-SafeAppDirectory {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )

    if ([string]::IsNullOrWhiteSpace($Path)) {
        throw "Refusing to use an empty install path."
    }

    $resolved = [System.IO.Path]::GetFullPath($Path)
    $root = [System.IO.Path]::GetPathRoot($resolved)
    if ($resolved -eq $root) {
        throw "Refusing to remove a filesystem root: $resolved"
    }

    $leaf = Split-Path -Path $resolved -Leaf
    if ($leaf -ne $AppName) {
        throw "Refusing to remove an unexpected install path. Expected the final folder name to be '$AppName': $resolved"
    }
}

function Assert-SafeStartMenuDirectory {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )

    if ([string]::IsNullOrWhiteSpace($Path)) {
        throw "Refusing to use an empty Start Menu path."
    }

    $resolved = [System.IO.Path]::GetFullPath($Path)
    $root = [System.IO.Path]::GetPathRoot($resolved)
    if ($resolved -eq $root) {
        throw "Refusing to remove a filesystem root: $resolved"
    }

    $leaf = Split-Path -Path $resolved -Leaf
    if ($leaf -ne $AppName) {
        throw "Refusing to remove an unexpected Start Menu folder: $resolved"
    }
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
$updateScriptInAppDir = if ($metadata.PSObject.Properties.Name -contains "update_script_app_dir") { $metadata.update_script_app_dir } else { Join-Path $installDir "update-ytdlp-tui.ps1" }
Assert-SafeAppDirectory -Path $installDir
Assert-SafeStartMenuDirectory -Path $startMenuDir

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

$installedUpdater = Join-Path $InstallerStateDir "update-ytdlp-tui.ps1"
if (Test-Path $installedUpdater) {
    Remove-Item $installedUpdater -Force
}

if (Test-Path $updateScriptInAppDir) {
    Remove-Item $updateScriptInAppDir -Force
}

if ((Test-Path $InstallerStateDir) -and -not (Get-ChildItem $InstallerStateDir -Force | Select-Object -First 1)) {
    Remove-Item $InstallerStateDir -Force
}

Write-Step "Uninstall complete."
