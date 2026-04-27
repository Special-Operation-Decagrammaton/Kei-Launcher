# Kei Launcher

[![Build Status](https://github.com/Special-Operation-Decagrammaton/Kei-Launcher/actions/workflows/build.yml/badge.svg)](https://github.com/Special-Operation-Decagrammaton/Kei-Launcher/actions)
[![Latest Release](https://img.shields.io/github/v/release/Special-Operation-Decagrammaton/Kei-Launcher)](https://github.com/Special-Operation-Decagrammaton/Kei-Launcher/releases)

`Kei Launcher` is a GUI utility that synchronizes local game files with translated assets provided by the [BA-TL-Assets](https://github.com/Special-Operation-Decagrammaton/BA-TL-Assets) repository.

> [!WARNING]
> **UNOFFICIAL TOOL & BAN RISK**
> This is a fan-made utility and is **not** affiliated with Nexon, NAT Games, or Yostar. 
> 
> * **Account Safety:** Modifying game files is a violation of most Terms of Service. Use of this tool carries a risk of account suspension or permanent ban.
> * **Liability:** By using this software, you agree that the developers of `Kei Launcher` are not responsible for any loss of data or account access.
> * **Scope:** This tool only modifies localization assets; it does not bypass anti-cheat or modify game logic.

---

## Technical Workflow
1. **Manifest Retrieval:** Fetches the current `GameManifest.json` from the Assets repository.
2. **Delta Check:** Compares local file hashes against the manifest to identify required updates.
3. **Synchronization:** Downloads and applies modified assets based on user-selected branches.

## Project Structure
The launcher is part of a multi-stage localization pipeline:

* **[BA-TL-Assets](https://github.com/Special-Operation-Decagrammaton/BA-TL-Assets):** The source for compiled, game-ready assets and version manifests.
* **[BA-TL-TEXT](https://github.com/Special-Operation-Decagrammaton/BA-TL-TEXT):** The community workspace for translation source files.
* **[BA-RAW-TEXT](https://github.com/Special-Operation-Decagrammaton/BA-RAW-TEXT):** Reference repository containing raw localization dumps for version comparison.

## Features
- **Automated Versioning:** Uses manifest-based updates to minimize bandwidth usage.
- **Branch Support:** Toggle between "Vanilla Global" and "Community Enhanced" translations.
- **File Validation:** Verifies the integrity of applied patches.
- **Cross-Platform:** Native support for Windows and Linux.

## Installation

### Windows
1. Download the latest `Kei_Launcher_windows.exe` from [Releases](https://github.com/Special-Operation-Decagrammaton/Kei-Launcher/releases).
2. Execute the file and select your game installation directory.

### Linux
1. Download `Kei_Launcher_linux` from [Releases](https://github.com/Special-Operation-Decagrammaton/Kei-Launcher/releases).
2. Set execution permissions: `chmod +x Kei_Launcher_linux`
3. Execute the binary.
