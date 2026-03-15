Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Clear-Host

$AppName = "ytdlp-tui"
$RepoOwner = "Txaverria"
$RepoName = "ytdlp_tui"
$AssetName = "ytdlp-tui-windows-amd64.zip"
$InstallerStateDir = Join-Path $env:LOCALAPPDATA "ytdlp-tui-installer"
$MetadataPath = Join-Path $InstallerStateDir "install.json"
$UninstallScriptInstalled = Join-Path $InstallerStateDir "uninstall-ytdlp-tui.ps1"
$UpdateScriptInstalled = Join-Path $InstallerStateDir "update-ytdlp-tui.ps1"

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
        throw "Refusing to use a filesystem root as the install path: $resolved"
    }

    $leaf = Split-Path -Path $resolved -Leaf
    if ($leaf -ne $AppName) {
        throw "Refusing to use an unexpected install path. Expected the final folder name to be '$AppName': $resolved"
    }
}

function Load-Metadata {
    if (-not (Test-Path $MetadataPath)) {
        throw "Installation metadata was not found. Install the app first."
    }
    return Get-Content -Path $MetadataPath -Raw | ConvertFrom-Json
}

function Get-LatestReleaseAsset {
    $headers = @{
        "User-Agent" = "$AppName-updater"
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

function Get-ScriptUrl {
    param(
        [Parameter(Mandatory = $true)][string]$Version,
        [Parameter(Mandatory = $true)][string]$ScriptName
    )

    return "https://raw.githubusercontent.com/$RepoOwner/$RepoName/$Version/scripts/windows/$ScriptName"
}

function Copy-AppBundle {
    param(
        [Parameter(Mandatory = $true)][string]$SourceDir,
        [Parameter(Mandatory = $true)][string]$DestinationDir
    )

    if (Test-Path $DestinationDir) {
        Assert-SafeAppDirectory -Path $DestinationDir
        Remove-Item $DestinationDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $DestinationDir -Force | Out-Null
    Copy-Item (Join-Path $SourceDir "*") $DestinationDir -Recurse -Force
}

$tempRoot = $null
try {
    $metadata = Load-Metadata
    $installDir = $metadata.install_dir
    $currentVersion = $metadata.version
    $UpdateScriptInAppDir = Join-Path $installDir "update-ytdlp-tui.ps1"
    Assert-SafeAppDirectory -Path $installDir

    Write-Host ""
    Write-Host "Installed version: $currentVersion"

    $asset = Get-LatestReleaseAsset
    Write-Host "Latest version:    $($asset.Version)"
    Write-Host ""

    if ($asset.Version -eq $currentVersion) {
        Write-Step "The app is already up to date."
        return
    }

    Write-Host "The app will be updated in:"
    Write-Host "  $installDir"
    Write-Host ""
    Write-Host "Type UPDATE to continue or CANCEL to stop"
    $choice = Read-Host "> "
    if ($choice -ne "UPDATE") {
        Write-Step "Update cancelled."
        return
    }

    $tempRoot = Join-Path $env:TEMP "$AppName-update-$([guid]::NewGuid().ToString('N'))"
    $zipPath = Join-Path $tempRoot $AssetName
    $extractDir = Join-Path $tempRoot "extract"

    New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
    New-Item -ItemType Directory -Path $extractDir -Force | Out-Null
    New-Item -ItemType Directory -Path $InstallerStateDir -Force | Out-Null

    Write-Step "Downloading $($asset.Version)..."
    Invoke-WebRequest -Uri $asset.Url -OutFile $zipPath

    Write-Step "Extracting release archive..."
    Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force

    $exePath = Get-ChildItem -Path $extractDir -Recurse -Filter "$AppName.exe" | Select-Object -First 1
    if (-not $exePath) {
        throw "Could not find $AppName.exe inside the downloaded archive."
    }

    $sourceDir = $exePath.DirectoryName
    Write-Step "Updating installed app..."
    Copy-AppBundle -SourceDir $sourceDir -DestinationDir $installDir

    Write-Step "Refreshing installed scripts..."
    Invoke-WebRequest -Uri (Get-ScriptUrl -Version $asset.Version -ScriptName "uninstall-ytdlp-tui.ps1") -OutFile $UninstallScriptInstalled
    Invoke-WebRequest -Uri (Get-ScriptUrl -Version $asset.Version -ScriptName "update-ytdlp-tui.ps1") -OutFile $UpdateScriptInstalled
    Copy-Item $UpdateScriptInstalled $UpdateScriptInAppDir -Force

    $metadata.version = $asset.Version
    $metadata.uninstall_script = $UninstallScriptInstalled
    $metadata.update_script = $UpdateScriptInstalled
    $metadata.update_script_app_dir = $UpdateScriptInAppDir
    $metadata | ConvertTo-Json | Set-Content -Path $MetadataPath -Encoding UTF8

    Write-Step "Update complete."
} catch {
    Write-Host ""
    Write-Host "Update failed: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    if ($tempRoot -and (Test-Path $tempRoot)) {
        Remove-Item $tempRoot -Recurse -Force
    }
    Write-Host ""
    Read-Host "Press Enter to close"
}
