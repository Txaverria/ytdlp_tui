@echo off
REM Launch PowerShell script with bypass so users can double-click
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0yt-dlp-launcher.ps1"