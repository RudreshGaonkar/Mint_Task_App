<div align="center">
  <img src="mint_tasks_icon.svg" alt="Mint Tasks Logo" width="80" height="80" />
  <h1>Mint Tasks</h1>
  <p><strong>Ultra-fast, native Google Tasks alternative and tabbed scratchpad, built for privacy and performance on Linux Mint, Ubuntu, and Debian.</strong></p>

  <p>
    <a href="https://linuxmint.com"><img src="https://img.shields.io/badge/Platform-Linux%20Mint%20%7C%20Ubuntu%20%7C%20Debian-green.svg" alt="Platform" /></a>
    <a href="https://riverbankcomputing.com/software/pyqt/"><img src="https://img.shields.io/badge/GUI-PyQt6-41CD52.svg" alt="Toolkit: PyQt6" /></a>
    <img src="https://img.shields.io/badge/RAM-35--65%20MB-brightgreen.svg" alt="RAM: 35-65MB" />
    <img src="https://img.shields.io/badge/Privacy-100%25%20Local%20SQLite-purple.svg" alt="100% Local Privacy" />
  </p>
</div>

---

## ⚡ Overview

**Mint Tasks** is a lightweight, privacy-focused native desktop productivity app designed specifically for Linux desktop environments (Cinnamon, XFCE, MATE, GNOME, KDE). 

Combining the minimalist workflow of **Google Tasks** with a modern **Windows 11-style multi-tab scratchpad/notepad**, Mint Tasks eliminates the bloat of Electron runtimes while delivering native C++ Qt rendering, 30-second background reminder alerts, and strict POSIX file permissions.

---

## ✨ Key Features

- **🚀 Ultra-Low Resource Footprint (35 MB – 65 MB RAM)**: Pure Python 3 and native PyQt6 bindings. No Chromium, No Electron, No memory bloat.
- **📋 Google Tasks Simplicity & Parity**:
  - Top-level tasks and collapsible nested subtasks with independent completion states.
  - Starred priority sorting and quick-add bar.
  - Due date & time picker (`QDateTimeEdit`) with color-coded badges (Overdue, Today, Upcoming).
- **🔔 Native Desktop Alerts & Reminders**:
  - Background daemon checks due tasks every 30 seconds.
  - Dispatches non-intrusive desktop notifications via `notify-send` / DBus and system audio alerts.
- **📝 Multi-Tab Notes Editor (Win11 Notepad Style)**:
  - Dynamic tabs with `Ctrl+N` (New Tab), `Ctrl+W` (Close Tab), `Ctrl+S` (Save), `Ctrl+Shift+S` (Save As), and `Ctrl+O` (Open).
  - Format-agnostic editing (`.txt`, `.md`, `.py`, `.sh`, `.json`, `.yaml`, `.csv`, `.log`, or extensionless).
  - Unsaved modifications indicator (`*`) and safe exit confirmations.
  - Live status bar tracking Line/Col position, word count, character count, and UTF-8 encoding.
- **🔒 True Hard Purge & Local SQLite Privacy**:
  - 100% offline local SQLite storage with Write-Ahead Logging (`WAL` mode).
  - Strict POSIX permissions: `0700` (`rwx------`) on directories and `0600` (`rw-------`) on database files.
  - **Permanent Hard Purge**: "Delete Permanently" directly executes SQL `DELETE` queries.
  - **Factory Reset**: Instant one-click wipe restoring pristine out-of-the-box state.
- **🎨 Minimalist Dark & Light Themes**: Catppuccin-inspired dark theme and clean light theme with System Tray integration (`QSystemTrayIcon`).

---

## 🚀 Installation

Mint Tasks installs in standard user space without requiring `sudo` privileges.

### 1. Clone the Repository
```bash
git clone https://github.com/RudreshGaonkar/Mint_Task_App.git
cd Mint_Task_App
```

### 2. Run the Setup Script
```bash
chmod +x install.sh
./install.sh
```

The installer will:
1. Create secure directories in `~/.local/share/mint_tasks/` with `0700` permissions.
2. Initialize an isolated virtual environment and install dependencies.
3. Install high-resolution vector icons to `~/.local/share/icons/hicolor/scalable/apps/`.
4. Register the `.desktop` launcher in `~/.local/share/applications/` so Mint Tasks appears immediately in your system Application Menu.

---

## 🔧 Troubleshooting & Prerequisites

### Missing `python3-venv`
On Ubuntu / Debian / Linux Mint minimal installations, ensure Python virtual environment tools are installed:

```bash
sudo apt update
sudo apt install python3-venv python3-pip
```
Then rerun `./install.sh`.

---

## 🗑️ Uninstallation

To completely remove Mint Tasks and permanently purge all SQLite databases, configuration files, cache, and desktop entries:

```bash
chmod +x uninstall.sh
./uninstall.sh
```

---

## 📁 Storage Architecture (XDG Compliance)

| Location | Purpose | Permissions |
| :--- | :--- | :--- |
| `~/.local/share/mint_tasks/tasks.db` | SQLite Database (`WAL` mode) | `0600` |
| `~/.config/mint_tasks/config.json` | Theme and Application Preferences | `0600` |
| `~/.cache/mint_tasks/` | Cache and Temporary Data | `0700` |
| `~/.local/share/applications/mint_tasks.desktop` | Desktop Entry Launcher | User |
| `~/.local/share/icons/hicolor/scalable/apps/mint-tasks.svg` | Scalable Vector Icon | User |
