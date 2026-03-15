# ytdlp-tui

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Textual](https://img.shields.io/badge/UI-Textual-5A2FC2)](https://textual.textualize.io/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Build](https://img.shields.io/github/actions/workflow/status/Txaverria/ytdlp-tui/release.yml?label=build)](https://github.com/Txaverria/ytdlp-tui/actions/workflows/release.yml)
[![Version](https://img.shields.io/badge/version-0.1.0-orange.svg)](https://github.com/Txaverria/ytdlp-tui/releases)

![ytdlp-tui screenshot](docs/assets/screenshot.png)

Cross-platform terminal UI for `yt-dlp`, built with Python and Textual.

`ytdlp-tui` is a fast, keyboard-friendly interface for downloading audio and video with `yt-dlp` without managing command flags manually. It provides a clean terminal workflow, live progress and logs, managed dependency installation on Windows, and simple settings for download location and runtime requirements like Deno.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Build a Release](#build-a-release)
- [License](#license)

## Features

- Clean TUI for video and audio downloads
- Multi-link input support
- Format presets: `mp3`, `m4a`, `ogg`, `mp4`, `webm`
- Quality presets: `high`, `medium`, `low`
- Live log output and progress states
- Managed `yt-dlp` install/update
- Windows-first managed `ffmpeg` install/update

## Tech Stack

- Python 3.11+
- Textual
- yt-dlp
- ffmpeg / ffprobe

## Installation

Prerequisites:

- Python 3.11 or newer
- On Linux/macOS, `yt-dlp` and `ffmpeg` are recommended on `PATH`
- On Windows, the app can install managed `yt-dlp` and `ffmpeg` for you
- For some YouTube downloads, `Deno` may also be required

Clone and run locally:

```bash
git clone https://github.com/Txaverria/ytdlp-tui.git
cd ytdlp-tui
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m ytdlp_tui
```

On Windows PowerShell:

```powershell
git clone https://github.com/Txaverria/ytdlp-tui.git
cd ytdlp-tui
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m ytdlp_tui
```

## YouTube Note

Some YouTube downloads may require [`Deno`](https://deno.com/) for JavaScript runtime support. If YouTube still blocks a request after Deno is installed, browser cookies may also be required.

## Usage

Download a single item:

```bash
python -m ytdlp_tui
```

Inside the app:

- paste one or more URLs into the input
- choose a format: `mp3`, `m4a`, `ogg`, `mp4`, `webm`
- choose a quality: `high`, `medium`, `low`
- press `Download`

Examples of accepted input:

```text
https://www.youtube.com/watch?v=example123
```

```text
https://www.youtube.com/watch?v=example123
https://www.youtube.com/watch?v=example456
```

```text
https://www.youtube.com/watch?v=example123, https://www.youtube.com/watch?v=example456
```

Expected behavior:

- live download progress in the status row
- live log output in the log panel
- automatic post-processing states such as converting, merging, or remuxing
- on Windows, missing `yt-dlp` or `ffmpeg` can be installed through the app

## Build a Release

```bash
python -m pip install .[build]
python scripts/package_release.py
```

Build output is written to `dist/`.

## License

MIT. See [`LICENSE`](./LICENSE).
