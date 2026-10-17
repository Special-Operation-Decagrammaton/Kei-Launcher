# Kei Launcher

<div align="center">

![Kei Launcher Icon](Assets/Icon/kei.ico)

**A high-performance, cross-platform translation patch launcher for Blue Archive (JP).**

[![Build Status](https://github.com/Special-Operation-Decagrammaton/Kei-Launcher/actions/workflows/build.yml/badge.svg)](https://github.com/Special-Operation-Decagrammaton/Kei-Launcher/actions)
[![Latest Release](https://img.shields.io/github/v/release/Special-Operation-Decagrammaton/Kei-Launcher?color=0284c7)](https://github.com/Special-Operation-Decagrammaton/Kei-Launcher/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-38bdf8)](https://github.com/Special-Operation-Decagrammaton/Kei-Launcher/releases)

</div>

---

> [!WARNING]
> **UNOFFICIAL TOOL & DISCLAIMER**
> 
> *Kei Launcher* is a fan-made community utility and is **not** affiliated with Nexon, NAT Games, NEXON Games, or Yostar.
> - **Account Safety:** Modifying game assets may violate game Terms of Service. Use at your own discretion and risk.
> - **Liability:** The developers and contributors of *Kei Launcher* assume no responsibility for account bans, suspensions, or data loss.
> - **Scope:** This utility synchronizes client localization text assets only. It does not tamper with game memory, executables, or anti-cheat mechanisms.

---

## Features

- 🌐 **Multi-Branch Translation:** Switch seamlessly between translation branches:
  - `en-ori` — Follows official global English translation.
  - `en-ext` — Extended community-enhanced English translation.
  - `pt-br` — Brazilian Portuguese community localization.
- ↩️ **Safe Revert / Uninstall:** Reverts translated files back to original game assets using cached backup URLs.
- 🌍 **Multi-Language UI:** Built-in localization support for both English and Portuguese.

---

## Installation

Download the latest release for your platform from [Releases](https://github.com/Special-Operation-Decagrammaton/Kei-Launcher/releases).

### Windows (x64)
1. Download `KeiLauncher-Windows-x64.zip`.
2. Extract the archive into a folder of your choice.
3. Run `KeiLauncher.exe`.
4. Click **Set Folder Location** and select your `BlueArchive_JP` installation directory (the folder containing `BlueArchive.exe` and `run.bat`).

### Linux (x64)
1. Download `KeiLauncher-Linux-x64.tar.gz`.
2. Extract the archive:
   ```bash
   tar -xzf KeiLauncher-Linux-x64.tar.gz -C ~/KeiLauncher
   ```
3. Mark executable and run:
   ```bash
   chmod +x ~/KeiLauncher/KeiLauncher
   ~/KeiLauncher/KeiLauncher
   ```

---

## Pipeline Architecture

*Kei Launcher* operates as the client-facing distribution layer in the localization ecosystem:

| Repository | Purpose |
|---|---|
| **[Kei-Launcher](https://github.com/Special-Operation-Decagrammaton/Kei-Launcher)** | Cross-platform desktop patcher and game launcher. |
| **[Build-Assets](https://github.com/Special-Operation-Decagrammaton/Build-Assets)** | Automated build artifacts, compiled game assets, and version manifests. |
| **[TL-TEXT](https://github.com/Special-Operation-Decagrammaton/TL-TEXT)** | Community translation repository and collaboration workspace. |
| **[RAW-TEXT](https://github.com/Special-Operation-Decagrammaton/RAW-TEXT)** | Extracted original game text dumps for diffing and revision tracking. |

---

## Building from Source

### Prerequisites
- [.NET 10 SDK](https://dotnet.microsoft.com/download/dotnet/10.0)
- Windows: Desktop development tools (MSVC C++ linker for Native AOT)
- Linux: `clang`, `zlib1g-dev`, `libx11-dev`, `libfontconfig1`

### Commands
```bash
# Clone the repository
git clone https://github.com/Special-Operation-Decagrammaton/Kei-Launcher.git
cd Kei-Launcher

# Restore & run in debug mode
dotnet run

# Build release bundle (Native AOT)
# Windows
dotnet publish -r win-x64 -c Release -o publish-win

# Linux
dotnet publish -r linux-x64 -c Release -o publish-linux
```

---

## Credits & Attribution

All assets are the intellectual property and copyright of **Nexon Games Co., Ltd.** and **Yostar (Hong Kong) Limited**. This project does not claim any ownership over these assets.
