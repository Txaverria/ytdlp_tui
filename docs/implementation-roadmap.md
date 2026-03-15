# Implementation Roadmap

## Product Direction

This repo is being rebuilt as a Python + Textual application instead of extending the current PowerShell launcher.

## Platform Policy

### Linux

- Prefer `yt-dlp` from the user's system
- Prefer `ffmpeg` from the user's system
- Offer managed installs later only as a fallback

### macOS

- Prefer `yt-dlp` from the user's system
- Prefer `ffmpeg` from the user's system
- Offer managed installs later only as a fallback

### Windows

- Default to managed `yt-dlp`
- Default to managed `ffmpeg`
- Avoid requiring users to preinstall either dependency

## Planned Commit Sequence

1. Bootstrap the Python/Textual repo and preserve the legacy launcher.
2. Add the main app shell, screens, and persisted settings.
3. Add platform-aware path handling and file/folder open actions.
4. Add download job execution and in-app progress/logging.
5. Add `yt-dlp` discovery and management policy by platform.
6. Add `ffmpeg` discovery and management policy by platform.
7. Add GitHub packaging and release automation.

## First Milestone

The first milestone is a runnable Textual app with:

- a main download screen
- a settings screen
- persistent app settings
- platform-aware dependency policy

No actual downloading happens in milestone one; that comes after the UI shell is stable.
