# Implementation Roadmap

## Current State

`ytdlp-tui` is a working Python + Textual application with:

- a main download screen
- a settings screen
- persisted download format and quality defaults
- Windows-managed `yt-dlp` and `ffmpeg` install flows
- live download progress, logs, and post-processing states
- packaged build automation through GitHub Actions

## Platform Policy

### Linux

- Prefer system `yt-dlp`
- Prefer system `ffmpeg`
- Detect `Deno` when available

### macOS

- Prefer system `yt-dlp`
- Prefer system `ffmpeg`
- Detect `Deno` when available

### Windows

- Support managed `yt-dlp` installation
- Support managed `ffmpeg` and `ffprobe` installation
- Store managed binaries in a local `bin/` directory for portable use
- Detect `Deno` when available

## Current Focus

The current work is release-oriented rather than foundational. The app is already functional, so the remaining work is mainly:

- packaged build validation on all target platforms
- release workflow improvements
- runtime edge-case handling
- documentation and release polish

## Near-Term Tasks

1. Validate packaged artifacts on Windows, macOS, and Linux.
2. Improve handling for terminal interrupts such as `Ctrl+C`.
3. Consider publishing GitHub Releases automatically from tag builds.
4. Continue refining dependency guidance for YouTube, Deno, and browser cookies.
5. Keep README and release instructions aligned with actual behavior.