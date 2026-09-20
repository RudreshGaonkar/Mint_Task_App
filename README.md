# 🌿 Mint Tasks: Lightweight Linux To-Do & Multi-Tab Notepad App

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Linux](https://img.shields.io/badge/Platform-Linux%20Mint%20%7C%20Ubuntu%20%7C%20Debian-green.svg)](https://linuxmint.com)
[![Toolkit: PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52.svg)](https://riverbankcomputing.com/software/pyqt/)
[![RAM: 35MB-65MB](https://img.shields.io/badge/Memory-35--65%20MB%20RAM-brightgreen.svg)]()
[![Privacy: 100% Local](https://img.shields.io/badge/Privacy-100%25%20Local%20SQLite-purple.svg)]()

> **The ultra-fast, native Google Tasks alternative and tabbed scratchpad built specifically for Linux Mint, Ubuntu, Debian, and all modern Linux desktops (Cinnamon, XFCE, MATE, GNOME, KDE).**

---

## ⚡ Why Mint Tasks?

Modern productivity apps are weighed down by bloated Electron/Chromium runtimes consuming hundreds of megabytes of RAM and sending telemetry to cloud servers. **Mint Tasks** is engineered from scratch as a native, lightweight, and privacy-first desktop utility with an ultra-low footprint (**35 MB – 65 MB RAM**).

It pairs the intuitive simplicity of **Google Tasks** with the versatility of a **Windows 11-style tabbed scratchpad/notepad**.

---

## ✨ Key Features

### 📋 1. Google Tasks-Inspired Task Manager
- **Minimalist Aesthetics**: Clean card layout, subtle borders, and fluid strike-through animations.
- **Hierarchical Subtasks**: Create and manage collapsible subtasks nested under parent tasks with independent completion tracking.
- **Scheduled Alerts & Desktop Notifications**: Integrated date & time pickers with a background daemon checking due tasks and triggering native `notify-send` alerts and non-intrusive sound cues.
- **Starred & Priority Sorting**: Pin crucial tasks to the top with one-click star prioritization.
- **Completed History & Restoration**: Archive completed tasks grouped by date, with one-click restore back to active status.

### 📝 2. Windows 11-Style Multi-Tab Notes & Scratchpad
- **Tabbed Document Workspace**: Open multiple notes simultaneously with keyboard shortcuts (`Ctrl+N` for new tab, `Ctrl+W` to close tab).
- **Format Agnostic**: Seamlessly open, edit, and save any plain text file supported on Linux (`.txt`, `.md`, `.py`, `.sh`, `.json`, `.yaml`, `.csv`, `.log`, or extensionless).
- **Unsaved Changes Protection**: Visual modified indicator (`*`) in tab headers and intelligent confirmation prompts before closing tabs or exiting.
- **Real-Time Editor Stats**: Clean status bar showing current line/column (`Ln X, Col Y`), word count, character count, and UTF-8 encoding.

### 🔒 3. Hardened Security & 100% Local Privacy
- **No Cloud, No Telemetry**: All data remains strictly on your machine in a local SQLite database configured with Write-Ahead Logging (`WAL` mode).
- **Strict POSIX Permissions**: Database files are locked down with `0600` (`rw-------`) and data directories with `0700` (`rwx------`), isolating your tasks from other users on multi-user systems.
- **True Hard Purge**: "Delete Permanently" immediately executes SQL `DELETE` queries to scrub data rather than applying soft flags.
- **Least Privilege Execution**: Operates entirely in standard user space—**no `sudo` required**.

### 🎨 4. Adaptive Dark & Light Themes
- **Google Tasks-Style Clean Theme Engine**: Built-in Dark Mode (`#1e1e2e` Catppuccin-inspired) and Light Mode (`#f8f9fa` crisp minimalist).
- **System Tray Integration**: Quietly minimizes to the system tray (`QSystemTrayIcon`) to keep reminder alerts running in the background without cluttering your panel.
- **Fully Responsive**: Adapts seamlessly from compact 380px panels to 4K widescreen displays.

---

## 🚀 Quick Start & Installation

Install **Mint Tasks** locally for your current user in seconds.

### Step 1: Clone Repository
```bash
git clone https://github.com/your-username/mint-tasks.git
cd mint-tasks
```

### Step 2: Run User Installer (No `sudo` needed)
```bash
chmod +x install.sh
./install.sh
```

The installer will:
1. Initialize secure storage at `~/.local/share/mint_tasks/`.
2. Set up an isolated Python virtual environment with `PyQt6`.
3. Install high-resolution application icons and the `.desktop` launcher.
4. Add **Mint Tasks** directly to your Linux Mint / desktop Application Menu under **Accessories / Office / Utilities**.

---

## 🔧 Troubleshooting & Prerequisites

### Missing `python3-venv` on Debian / Ubuntu / Linux Mint
If the installer reports that `ensurepip` or `venv` is missing, install standard Python venv support:

```bash
sudo apt update
sudo apt install python3-venv python3-pip
```
Then rerun `./install.sh`.

### Running Directly in Development Mode
You can also launch Mint Tasks directly from your local terminal:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

---

## 🗑️ Complete Uninstallation & Data Purge

To completely wipe Mint Tasks, all stored databases, configurations, cache, desktop shortcuts, and icons:

```bash
chmod +x uninstall.sh
./uninstall.sh
```

---

## 📁 Storage Architecture (XDG Base Directory Compliance)

| Path | Description | Permissions |
| :--- | :--- | :--- |
| `~/.local/share/mint_tasks/tasks.db` | Local SQLite task & subtask database (WAL mode) | `0600` |
| `~/.config/mint_tasks/config.json` | Theme and user preference configuration | `0600` |
| `~/.cache/mint_tasks/` | Cache directory | `0700` |
| `~/.local/share/applications/mint_tasks.desktop` | Application menu launcher | User |
| `~/.local/share/icons/hicolor/scalable/apps/mint-tasks.svg` | Desktop vector icon | User |

---

## 📄 License

Distributed under the **MIT License**. Free and open-source for personal and professional use.
