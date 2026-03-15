# Release Process

## Goal

Produce downloadable build artifacts for Windows, macOS, and Linux without requiring end users to install Python.

## Current Approach

- Build native bundles with PyInstaller
- Run the build separately on each target OS in GitHub Actions
- Upload packaged artifacts from each runner

## Why This Approach

PyInstaller does not cross-compile. Windows builds must be produced on Windows, macOS builds on macOS, and Linux builds on Linux.

## Workflow

The workflow file is:

- [release.yml](/home/teaex/Coding/YT-DLP-PWSH-UI/.github/workflows/release.yml)

It runs on:

- manual dispatch
- tag push matching `v*`

## Local Build

```bash
python -m pip install .[build]
python scripts/package_release.py
```

## Current Output

- Windows: `.zip`
- macOS: `.tar.gz`
- Linux: `.tar.gz`

## Follow-up Work

- attach artifacts to GitHub Releases automatically
- test PyInstaller packaging behavior with Textual on each OS
- decide whether Linux should also ship an AppImage later
