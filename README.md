# ytdlp-tui

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Textual](https://img.shields.io/badge/UI-Textual-5A2FC2)](https://textual.textualize.io/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Build](https://img.shields.io/github/actions/workflow/status/Txaverria/ytdlp-tui/release.yml?label=build)](https://github.com/Txaverria/ytdlp-tui/actions/workflows/release.yml)

```text
 █████ █████ ███████████ ██████████   █████       ███████████                   ███████████ █████  █████ █████
▒▒███ ▒▒███ ▒█▒▒▒███▒▒▒█▒▒███▒▒▒▒███ ▒▒███       ▒▒███▒▒▒▒▒███                 ▒█▒▒▒███▒▒▒█▒▒███  ▒▒███ ▒▒███
 ▒▒███ ███  ▒   ▒███  ▒  ▒███   ▒▒███ ▒███        ▒███    ▒███                 ▒   ▒███  ▒  ▒███   ▒███  ▒███
  ▒▒█████       ▒███     ▒███    ▒███ ▒███        ▒██████████     ██████████       ▒███     ▒███   ▒███  ▒███
   ▒▒███        ▒███     ▒███    ▒███ ▒███        ▒███▒▒▒▒▒▒     ▒▒▒▒▒▒▒▒▒▒        ▒███     ▒███   ▒███  ▒███
    ▒███        ▒███     ▒███    ███  ▒███      █ ▒███                             ▒███     ▒███   ▒███  ▒███
    █████       █████    ██████████   ███████████ █████                            █████    ▒▒████████   █████
   ▒▒▒▒▒       ▒▒▒▒▒    ▒▒▒▒▒▒▒▒▒▒   ▒▒▒▒▒▒▒▒▒▒▒ ▒▒▒▒▒                            ▒▒▒▒▒      ▒▒▒▒▒▒▒▒   ▒▒▒▒▒
```

Cross-platform terminal UI for `yt-dlp`, built with Python and Textual.

## Features

- Clean TUI for video and audio downloads
- Multi-link input support
- Format presets: `mp3`, `m4a`, `ogg`, `mp4`, `webm`
- Quality presets: `high`, `medium`, `low`
- Live log output and progress states
- Managed `yt-dlp` install/update
- Windows-first managed `ffmpeg` install/update

## Platform Behavior

- Linux: prefer system `yt-dlp` and `ffmpeg`
- macOS: prefer system `yt-dlp` and `ffmpeg`
- Windows: managed installs are supported directly in the app

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m ytdlp_tui
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m ytdlp_tui
```

## Build a Release

```bash
python -m pip install .[build]
python scripts/package_release.py
```

Build output is written to `dist/`.

## GitHub Actions

GitHub Actions builds release bundles for Linux, macOS, and Windows from [`.github/workflows/release.yml`](./.github/workflows/release.yml).

## License

MIT. See [`LICENSE`](./LICENSE).
