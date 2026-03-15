# ytdlp-tui

Cross-platform terminal UI for `yt-dlp`, rebuilt around Python and Textual.

## Status

This repository is being rebuilt from a legacy Windows-only PowerShell launcher into a proper cross-platform app.

The legacy launcher is still present for reference:

- `yt-dlp-launcher.ps1`
- `launch.bat`

## Goals

- Fast, clean TUI for downloads
- Simple settings screen
- Cross-platform support for Linux, macOS, and Windows
- Sensible defaults for download location
- Easy access to downloaded files
- Managed updates where they help users most

## Dependency Policy

The app will handle `yt-dlp` and `ffmpeg` differently by platform:

- Linux: prefer the user's installed `yt-dlp` and `ffmpeg`
- macOS: prefer the user's installed `yt-dlp` and `ffmpeg`
- Windows: default to managed downloads for `yt-dlp` and `ffmpeg`

This matches the practical installation friction on each OS.

## Planned Features

- Main download screen with a single input field
- Audio/video/custom download presets
- Settings screen for download path and defaults
- Download history with open file/open folder actions
- `yt-dlp` install/update management
- `ffmpeg` detection and install/update management

## Development

The new app uses:

- Python
- Textual

Local run target:

```bash
python -m ytdlp_tui
```

Once packaging is in place, end users should not need to install Python separately.

## Roadmap

The active rebuild plan lives in [`docs/implementation-roadmap.md`](/home/teaex/Coding/YT-DLP-PWSH-UI/docs/implementation-roadmap.md).
