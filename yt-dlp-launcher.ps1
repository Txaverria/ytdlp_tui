# --- CONFIG ---
$Root = Split-Path -Parent $MyInvocation.MyCommand.Definition
try {
    Set-Location $Root
} catch {
    Write-Host "Warning: could not Set-Location to script root: $($_.Exception.Message)"
}

$SrcDir = Join-Path $Root "src"
$DownloadsDir = Join-Path $Root "Downloads"

$YTDLP_API = "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"
$GitHubHeaders = @{ "User-Agent" = "yt-dlp-launcher-script" }

# --- Ensure directories ---
foreach ($d in @($SrcDir, $DownloadsDir)) {
    try {
        if (-not (Test-Path $d)) {
            New-Item -ItemType Directory -Path $d | Out-Null
        }
    } catch {
        Write-Host "Error creating directory '$d': $($_.Exception.Message)"
        throw
    }
}

function Pause($Seconds = 1) {
    Start-Sleep -Seconds $Seconds
}

# --- Version checks ---
function Get-Local-YtDlpVersion {
    $exe = Join-Path $SrcDir "yt-dlp.exe"
    if (Test-Path $exe) {
        try {
            $ver = & $exe --version 2>$null
            if ($LASTEXITCODE -ne 0 -or -not $ver) { return $null }
            return $ver.Trim()
        } catch {
            return $null
        }
    }
    return $null
}

function Get-Local-FFmpegVersion {
    $exe = Join-Path $SrcDir "ffmpeg.exe"
    if (Test-Path $exe) {
        try {
            $out = (& $exe -version) -join "`n"
            if ($out -match "ffmpeg version\s+([^\s]+)") { return $Matches[1] }
            return $null
        } catch {
            return $null
        }
    }
    return $null
}

# --- Download helper ---
function Download-File($Url, $OutFile) {
    if (-not $Url) { throw "No URL provided to Download-File" }
    if (-not $OutFile) { throw "No OutFile provided to Download-File" }

    try {
        Write-Host "Downloading: $Url"
        Invoke-WebRequest -Uri $Url -Headers $GitHubHeaders -OutFile $OutFile -UseBasicParsing -ErrorAction Stop
    } catch {
        throw "Download failed for '$Url' -> $($_.Exception.Message)"
    }
}

# --- yt-dlp update ---
function Update-YtDlp {
    Clear-Host
    Write-Host "Checking yt-dlp updates..."

    try {
        $rel = Invoke-RestMethod -Uri $YTDLP_API -Headers $GitHubHeaders -ErrorAction Stop
        $latest = $rel.tag_name
        $asset = $rel.assets | Where-Object { $_.name -eq "yt-dlp.exe" } | Select-Object -First 1
        if (-not $asset) { throw "yt-dlp.exe not found in release assets." }

        $local = Get-Local-YtDlpVersion
        Write-Host "Latest: $latest"
        Write-Host "Local : $local"

        $localPath = Join-Path $SrcDir "yt-dlp.exe"

        if ($local -ne $latest -or -not (Test-Path $localPath)) {
            $tmp = Join-Path $env:TEMP "yt-dlp.exe"
            try {
                Download-File $asset.browser_download_url $tmp
                Move-Item -Force $tmp $localPath -ErrorAction Stop
                Write-Host "yt-dlp updated to $latest."
            } catch {
                throw "Failed to download/install yt-dlp: $($_.Exception.Message)"
            }
        }
        else {
            Write-Host "yt-dlp already up to date."
        }
    }
    catch {
        Write-Host "yt-dlp update failed: $($_.Exception.Message)"
    }

    Pause 2
}

# --- FFmpeg update ---
function Update-FFmpeg {
    Clear-Host
    Write-Host "Checking FFmpeg..."

    try {
        # Detect local ffmpeg version
        $localVersion = Get-Local-FFmpegVersion
        if ($localVersion) {
            Write-Host "Local FFmpeg detected: $localVersion"
            Write-Host "FFmpeg already installed. Skipping download."
            Pause 2
            return
        }

        Write-Host "FFmpeg not found. Installing..."

        $ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.7z"
        $sevenZipUrl = "https://www.7-zip.org/a/7zr.exe"

        $sevenZip = Join-Path $SrcDir "7z.exe"
        if (-not (Test-Path $sevenZip)) {
            try {
                Write-Host "Downloading 7-Zip..."
                Invoke-WebRequest $sevenZipUrl -OutFile $sevenZip -UseBasicParsing -ErrorAction Stop
            } catch {
                throw "Failed to download 7-Zip extractor: $($_.Exception.Message)"
            }
        }

        $tmp7z = Join-Path $env:TEMP "ffmpeg.7z"
        $tmpDir = Join-Path $env:TEMP ("ffmpeg_extract_" + [guid]::NewGuid().ToString())

        Write-Host "Downloading FFmpeg archive..."
        try {
            Invoke-WebRequest $ffmpegUrl -OutFile $tmp7z -UseBasicParsing -ErrorAction Stop
        } catch {
            throw "Failed to download FFmpeg archive: $($_.Exception.Message)"
        }

        Write-Host "Extracting FFmpeg..."
        try {
            # Ensure tmpDir exists
            if (-not (Test-Path $tmpDir)) { New-Item -ItemType Directory -Path $tmpDir | Out-Null }
            & $sevenZip x $tmp7z ("-o" + $tmpDir) -y | Out-Null
        } catch {
            throw "Failed to extract FFmpeg archive: $($_.Exception.Message)"
        }

        try {
            $bin = Get-ChildItem $tmpDir -Recurse -Directory -ErrorAction Stop | Where-Object Name -eq "bin" | Select-Object -First 1
            if (-not $bin) { throw "FFmpeg 'bin' folder not found after extraction." }

            $srcFfmpeg = Join-Path $bin.FullName "ffmpeg.exe"
            $srcFfprobe = Join-Path $bin.FullName "ffprobe.exe"
            $srcFplay = Join-Path $bin.FullName "ffplay.exe"

            Copy-Item $srcFfmpeg (Join-Path $SrcDir "ffmpeg.exe") -Force -ErrorAction Stop
            if (Test-Path $srcFfprobe) { Copy-Item $srcFfprobe (Join-Path $SrcDir "fprobe.exe") -Force -ErrorAction SilentlyContinue }
            if (Test-Path $srcFplay) { Copy-Item $srcFplay (Join-Path $SrcDir "fplay.exe") -Force -ErrorAction SilentlyContinue }
        } catch {
            throw "Failed to copy FFmpeg binaries: $($_.Exception.Message)"
        } finally {
            # cleanup where possible
            try { Remove-Item $tmp7z -Force -ErrorAction SilentlyContinue } catch {}
            try { Remove-Item $tmpDir -Recurse -Force -ErrorAction SilentlyContinue } catch {}
        }

        Write-Host "FFmpeg installed: $(Get-Local-FFmpegVersion)"
    }
    catch {
        Write-Host "FFmpeg installation failed: $($_.Exception.Message)"
    }

    Pause 2
}

function Update-All {
    try {
        Update-YtDlp
        Update-FFmpeg
    } catch {
        Write-Host "Update-All failed: $($_.Exception.Message)"
    }
}

# --- Download runner ---
function Run-DownloadMenu {
    Clear-Host

    $yt = Join-Path $SrcDir "yt-dlp.exe"
    if (-not (Test-Path $yt)) {
        Write-Host "yt-dlp not installed. Run update first."
        Pause 2
        return
    }

    try {
        $url = Read-Host "Paste URL (blank to cancel)"
    } catch {
        Write-Host "Input cancelled."
        return
    }

    if (-not $url) { return }

    Write-Host "1) Audio MP3 (best)"
    Write-Host "2) Audio MP3 (normal)"
    Write-Host "3) Video MP4 (best)"
    Write-Host "4) Video (no remux)"
    Write-Host "5) Custom arguments"

    try {
        $key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        $choice = $key.Character
    } catch {
        Write-Host "No input detected; cancelling."
        return
    }

    $outTemplate = Join-Path $DownloadsDir "%(title)s.%(ext)s"

    $tmpPrintFile = Join-Path $env:TEMP ("yt-dlp-path-" + [guid]::NewGuid().ToString() + ".txt")

    switch ($choice) {
        '1' { $args = "-x --audio-format mp3 --audio-quality 0" }
        '2' { $args = "-x --audio-format mp3 --audio-quality 5" }
        '3' { $args = "--remux-video mp4" }
        '4' { $args = "" }
        '5' { 
            try {
                $args = Read-Host "Enter full yt-dlp arguments"
            } catch {
                Write-Host "Custom args cancelled."
                return
            }
         }
        default {
            Write-Host "Invalid choice. Cancelling."
            Pause 1
            return
        }
    }

    Clear-Host
    Write-Host "Preparing to download..."
    Write-Host ""

    # Basic URL/file validation (best-effort): yt-dlp accepts many inputs so we won't block,
    # but we warn if it doesn't look like a URL or existing path.
    $looksLikeUrl = [uri]::IsWellFormedUriString($url, [uriKind]::Absolute)
    $looksLikeLocalPath = Test-Path $url

    if (-not $looksLikeUrl -and -not $looksLikeLocalPath) {
        Write-Host "Warning: input does not look like a well-formed URL or an existing local path."
        Write-Host "yt-dlp accepts search strings and platform-specific urls too; proceeding anyway."
        Pause 1
    }

    # Spinner while yt-dlp runs (PS5-safe)
    $spinner = @('|','/','-','\')
    $i = 0

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $yt
    # build arguments safely
    $escapedOut = $outTemplate -replace '"','\"'
    $escapedTmp = $tmpPrintFile -replace '"','\"'
    $psi.Arguments = "$args -o `"$escapedOut`" --print-to-file after_move:filepath `"$escapedTmp`" `"$url`""
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi

    try {
        if (-not $proc.Start()) {
            Write-Host "Failed to start yt-dlp process."
            Pause 2
            return
        }
    } catch {
        Write-Host "Error starting yt-dlp: $($_.Exception.Message)"
        return
    }

    try {
        while (-not $proc.HasExited) {
            Write-Host -NoNewline ("`rWorking " + $spinner[$i % $spinner.Count])
            $i++
            Start-Sleep -Milliseconds 150
        }

        Write-Host "`rWorking complete.    "

        # Read output from the already-finished process
        $stdout = $proc.StandardOutput.ReadToEnd()
        $stderr = $proc.StandardError.ReadToEnd()

        if ($proc.ExitCode -ne 0) {
            Write-Host "yt-dlp exited with code $($proc.ExitCode)."
            if ($stderr) {
                Write-Host "Error output:"
                Write-Host $stderr
            } elseif ($stdout) {
                Write-Host "Output:"
                Write-Host $stdout
            }
            Pause 3
            return
        }

    } catch {
        Write-Host "Error while running yt-dlp: $($_.Exception.Message)"
    }

    try {
        if (Test-Path $tmpPrintFile) {
            $files = Get-Content $tmpPrintFile | Where-Object { $_ -and (Test-Path $_) }
            try { Remove-Item $tmpPrintFile -Force -ErrorAction SilentlyContinue } catch {}
            if ($files -and $files.Count -gt 0) {
                Write-Host ""
                Write-Host "Downloaded file(s):"
                foreach ($f in $files) {
                    Write-Host " - $f"
                }
            }
            else {
                Write-Host "Download finished. Check: $DownloadsDir"
            }
        }
        else {
            Write-Host "Download finished. Check: $DownloadsDir"
        }
    } catch {
        Write-Host "Error determining downloaded files: $($_.Exception.Message)"
    }

    Pause 3
}

# --- MAIN MENU ---
while ($true) {
    try {
        Clear-Host
        Write-Host "yt-dlp Launcher"
        Write-Host "================"
        Write-Host "yt-dlp : $(Get-Local-YtDlpVersion)"
        Write-Host "ffmpeg : $(Get-Local-FFmpegVersion)"
        Write-Host ""
        Write-Host "1) Download"
        Write-Host "2) Update All"
        Write-Host "3) Exit"

        try {
            $key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            $opt = $key.Character
        } catch {
            Write-Host "Input failure - exiting."
            break
        }

        switch ($opt) {
            '1' { Run-DownloadMenu }
            '2' { Update-All }
            '3' { exit }
            default { Write-Host "Unknown option. Please press 1, 2 or 3."; Pause 1 }
        }
    } catch {
        Write-Host "Fatal error in main loop: $($_.Exception.Message)"
        Pause 2
    }
}
