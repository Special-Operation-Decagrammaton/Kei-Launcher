# BA-TL-Launcher

An automated patcher for Blue Archive JP localization.

[![Build Status](https://github.com/Special-Operation-Decagrammaton/BA-TL-Launcher/actions/workflows/build.yml/badge.svg)](https://github.com/Special-Operation-Decagrammaton/BA-TL-Launcher/actions)
[![Latest Release](https://img.shields.io/github/v/release/Special-Operation-Decagrammaton/BA-TL-Launcher)](https://github.com/Special-Operation-Decagrammaton/BA-TL-Launcher/releases)

`BA-TL-Launcher` is a GUI utility that synchronizes local game files with translated assets provided by the [BA-TL-Assets](https://github.com/Special-Operation-Decagrammaton/BA-TL-Assets) repository.

<img width="959" height="634" alt="image" src="https://github.com/user-attachments/assets/020ac4e4-1ac7-4616-8e98-d85793a39106" />

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
1. Download the latest `BA_TL_Launcher_windows.exe` from [Releases](https://github.com/Special-Operation-Decagrammaton/BA-TL-Launcher/releases).
2. Execute the file and select your game installation directory.

### Linux
1. Download `BA_TL_Launcher_linux` from [Releases](https://github.com/Special-Operation-Decagrammaton/BA-TL-Launcher/releases).
2. Set execution permissions: `chmod +x BA_TL_Launcher_linux`
3. Execute the binary.

## Disclaimer
- This is an unofficial fan-made tool and is not affiliated with Nexon, NAT Games, or Yostar.
- Modifying game files may carry a risk of account suspension.
- This utility does not distribute game binaries; it only modifies text-based assets.
