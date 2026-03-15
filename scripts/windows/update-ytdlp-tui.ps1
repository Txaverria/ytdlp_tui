param(
    [switch]$Relaunched
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Clear-Host
$shouldPause = $Relaunched

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

function Assert-AppNotRunning {
    $running = Get-Process -Name $AppName -ErrorAction SilentlyContinue
    if ($running) {
        throw "$AppName.exe is still running. Close the app before updating."
    }
}

function Replace-AppBundle {
    param(
        [Parameter(Mandatory = $true)][string]$SourceDir,
        [Parameter(Mandatory = $true)][string]$DestinationDir
    )

    Assert-SafeAppDirectory -Path $DestinationDir

    $backupDir = "$DestinationDir.old"
    if (Test-Path $backupDir) {
        Remove-Item $backupDir -Recurse -Force
    }

    if (Test-Path $DestinationDir) {
        try {
            Rename-Item -Path $DestinationDir -NewName (Split-Path -Path $backupDir -Leaf)
        } catch {
            throw "The install folder is in use. Close the app and any Explorer or terminal windows open in that folder, then try again."
        }
    }

    try {
        Copy-AppBundle -SourceDir $SourceDir -DestinationDir $DestinationDir
        if (Test-Path $backupDir) {
            Remove-Item $backupDir -Recurse -Force
        }
    } catch {
        if ((-not (Test-Path $DestinationDir)) -and (Test-Path $backupDir)) {
            Rename-Item -Path $backupDir -NewName (Split-Path -Path $DestinationDir -Leaf)
        }
        throw
    }
}

$currentScriptPath = if ($PSCommandPath) { [System.IO.Path]::GetFullPath($PSCommandPath) } else { "" }
$tempRoot = $null
try {
    $metadata = Load-Metadata
    $installDir = $metadata.install_dir
    $currentVersion = $metadata.version
    $UpdateScriptInAppDir = Join-Path $installDir "update-ytdlp-tui.ps1"
    Assert-SafeAppDirectory -Path $installDir

    $normalizedInstallDir = [System.IO.Path]::GetFullPath($installDir)
    $runningFromInstallDir = $false
    if ($currentScriptPath) {
        $scriptDirectory = Split-Path -Path $currentScriptPath -Parent
        $runningFromInstallDir = $scriptDirectory.StartsWith($normalizedInstallDir, [System.StringComparison]::OrdinalIgnoreCase)
    }

    if (-not $Relaunched -and $runningFromInstallDir) {
        $tempScript = Join-Path $env:TEMP "$AppName-updater-$([guid]::NewGuid().ToString('N')).ps1"
        Copy-Item $currentScriptPath $tempScript -Force
        Write-Step "Restarting updater from a temporary location..."
        Start-Process powershell.exe `
            -WorkingDirectory $env:TEMP `
            -ArgumentList @(
                "-ExecutionPolicy", "Bypass",
                "-File", $tempScript,
                "-Relaunched"
            ) | Out-Null
        exit 0
    }

    Set-Location $env:TEMP
    Assert-AppNotRunning

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
    Replace-AppBundle -SourceDir $sourceDir -DestinationDir $installDir

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
    if ($shouldPause) {
        Write-Host ""
        Read-Host "Press Enter to close"
    }
}
