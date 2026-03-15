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

## Release Steps

1. Commit and push the desired state to `main`.
2. Create a version tag locally:

```bash
git tag v0.1.0
git push origin v0.1.0
```

3. Wait for the GitHub Actions workflow to finish.
4. Download the platform artifact from the workflow run.
5. Validate the packaged build on the target OS before treating the release as final.

## Local Build

```bash
python -m pip install .[build]
python scripts/package_release.py
```

## Output

- Windows: `.zip`
- macOS: `.tar.gz`
- Linux: `.tar.gz`

## Current Limitations

- The workflow uploads artifacts but does not yet create a GitHub Release automatically.
- Packaged builds must still be tested manually on each target platform.
- PyInstaller output size and behavior should be treated as part of release validation.

## Follow-up Work

- attach artifacts to GitHub Releases automatically
- test PyInstaller packaging behavior with Textual on each OS
- decide whether Linux should also ship an AppImage later
