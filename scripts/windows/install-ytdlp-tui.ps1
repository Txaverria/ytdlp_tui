Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$AppName = "ytdlp-tui"
$RepoOwner = "Txaverria"
$RepoName = "ytdlp-tui"
$AssetName = "ytdlp-tui-windows-amd64.zip"
$InstallerStateDir = Join-Path $env:LOCALAPPDATA "ytdlp-tui-installer"
$MetadataPath = Join-Path $InstallerStateDir "install.json"
$UninstallScriptSource = Join-Path $PSScriptRoot "uninstall-ytdlp-tui.ps1"
$UninstallScriptInstalled = Join-Path $InstallerStateDir "uninstall-ytdlp-tui.ps1"

function Write-Step {
    param([string]$Message)
    Write-Host "[ytdlp-tui] $Message"
}

function Get-LatestReleaseAsset {
    $headers = @{
        "User-Agent" = "$AppName-installer"
        "Accept" = "application/vnd.github+json"
    }
    $release = Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/repos/$RepoOwner/$RepoName/releases/latest"
    $asset = $release.assets | Where-Object { $_.name -eq $AssetName } | Select-Object -First 1
    if (-not $asset) {
        throw "Could not find release asset '$AssetName' in the latest GitHub release."
    }
    return [PSCustomObject]@{
        Version = $release.tag_name
        Url = $asset.browser_download_url
    }
}

function Select-InstallDirectory {
    $localDir = Join-Path $env:LOCALAPPDATA "Programs\$AppName"
    $programFilesDir = Join-Path $env:ProgramFiles $AppName
    $currentDir = (Get-Location).Path

    Write-Host ""
    Write-Host "Choose an install location:"
    Write-Host "  1. Local AppData (recommended) - $localDir"
    Write-Host "  2. Program Files - $programFilesDir"
    Write-Host "  3. Custom folder"
    Write-Host "  4. Current folder - $currentDir"
    Write-Host ""

    while ($true) {
        $choice = Read-Host "Enter 1, 2, 3, or 4"
        switch ($choice) {
            "1" { return $localDir }
            "2" { return $programFilesDir }
            "3" {
                $customDir = Read-Host "Enter the full install path"
                if ([string]::IsNullOrWhiteSpace($customDir)) {
                    Write-Host "Path cannot be empty."
                    continue
                }
                return $customDir
            }
            "4" { return $currentDir }
            default { Write-Host "Invalid selection." }
        }
    }
}

function New-Shortcut {
    param(
        [Parameter(Mandatory = $true)][string]$ShortcutPath,
        [Parameter(Mandatory = $true)][string]$TargetPath,
        [string]$Arguments = "",
        [string]$WorkingDirectory = "",
        [string]$IconLocation = ""
    )

    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($ShortcutPath)
    $shortcut.TargetPath = $TargetPath
    $shortcut.Arguments = $Arguments
    if ($WorkingDirectory) { $shortcut.WorkingDirectory = $WorkingDirectory }
    if ($IconLocation) { $shortcut.IconLocation = $IconLocation }
    $shortcut.Save()
}

function Copy-AppBundle {
    param(
        [Parameter(Mandatory = $true)][string]$SourceDir,
        [Parameter(Mandatory = $true)][string]$DestinationDir
    )

    if (Test-Path $DestinationDir) {
        Remove-Item $DestinationDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $DestinationDir -Force | Out-Null
    Copy-Item (Join-Path $SourceDir "*") $DestinationDir -Recurse -Force
}

$installDir = Select-InstallDirectory
$tempRoot = Join-Path $env:TEMP "$AppName-install-$([guid]::NewGuid().ToString('N'))"
$zipPath = Join-Path $tempRoot $AssetName
$extractDir = Join-Path $tempRoot "extract"
$startMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\$AppName"
$appShortcut = Join-Path $startMenuDir "$AppName.lnk"
$uninstallShortcut = Join-Path $startMenuDir "Uninstall $AppName.lnk"

New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
New-Item -ItemType Directory -Path $extractDir -Force | Out-Null
New-Item -ItemType Directory -Path $InstallerStateDir -Force | Out-Null

try {
    Write-Step "Resolving latest release..."
    $asset = Get-LatestReleaseAsset

    Write-Step "Downloading $($asset.Version)..."
    Invoke-WebRequest -Uri $asset.Url -OutFile $zipPath

    Write-Step "Extracting release archive..."
    Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force

    $exePath = Get-ChildItem -Path $extractDir -Recurse -Filter "$AppName.exe" | Select-Object -First 1
    if (-not $exePath) {
        throw "Could not find $AppName.exe inside the downloaded archive."
    }

    $sourceDir = $exePath.DirectoryName
    Write-Step "Installing to $installDir"
    Copy-AppBundle -SourceDir $sourceDir -DestinationDir $installDir

    if (-not (Test-Path $UninstallScriptSource)) {
        throw "Could not find uninstall script next to the installer."
    }
    Copy-Item $UninstallScriptSource $UninstallScriptInstalled -Force

    New-Item -ItemType Directory -Path $startMenuDir -Force | Out-Null
    New-Shortcut -ShortcutPath $appShortcut -TargetPath (Join-Path $installDir "$AppName.exe") -WorkingDirectory $installDir -IconLocation (Join-Path $installDir "$AppName.exe")
    New-Shortcut -ShortcutPath $uninstallShortcut -TargetPath "powershell.exe" -Arguments "-ExecutionPolicy Bypass -File `"$UninstallScriptInstalled`"" -WorkingDirectory $InstallerStateDir -IconLocation (Join-Path $installDir "$AppName.exe")

    $metadata = [PSCustomObject]@{
        app_name = $AppName
        version = $asset.Version
        install_dir = $installDir
        start_menu_dir = $startMenuDir
        app_shortcut = $appShortcut
        uninstall_shortcut = $uninstallShortcut
        uninstall_script = $UninstallScriptInstalled
    }
    $metadata | ConvertTo-Json | Set-Content -Path $MetadataPath -Encoding UTF8

    Write-Step "Installation complete."
    Write-Host ""
    Write-Host "Installed to: $installDir"
    Write-Host "Start Menu shortcut: $appShortcut"
    Write-Host "Uninstall script: $UninstallScriptInstalled"
    Write-Host ""
    Write-Host "Note: some YouTube downloads may require Deno."
    Write-Host "Windows PowerShell install command:"
    Write-Host "  irm https://deno.land/install.ps1 | iex"
} finally {
    if (Test-Path $tempRoot) {
        Remove-Item $tempRoot -Recurse -Force
    }
}
