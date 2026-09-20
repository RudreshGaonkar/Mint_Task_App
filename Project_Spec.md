# TASK SPECIFICATION: Native Linux Mint Tasks & Multi-Tab Notes App

## 1. Project Overview & Objectives
Build a lightweight, highly secure, and responsive native desktop productivity suite for Linux Mint (Cinnamon/X11/Wayland). The application combines:
1. **Google Tasks Parity:** Minimalist UI, tasks, subtasks, scheduled time-based alerts, history tracking, and permanent hard-purge deletion.
2. **Multi-Tab Notes Editor:** Modern tabbed document workspace (Windows 11 Notepad style) supporting arbitrary file extensions.
3. **Low Resource Footprint:** Native Qt-based rendering consuming 35 MB to 65 MB RAM, avoiding bloated Electron/Chromium runtimes.
4. **Strict Security & Complete Lifecycle Management:** Least privilege execution, restrictive POSIX file permissions (`0600`), parameterized SQL queries, and a clean uninstaller that completely purges all local databases and configuration files.

---

## 2. Tech Stack & Audited Dependencies
- **Core Runtime:** Python 3 (standard library: `sqlite3`, `datetime`, `pathlib`, `os`, `subprocess`).
- **GUI Toolkit:** `PyQt6` (native C++ bindings, low memory, cross-resolution scaling).
- **Notifications:** Direct DBus integration (`org.freedesktop.Notifications`) or system `notify-send` via safe subprocess calls (`shell=False`).
- **Storage:** Local SQLite database with Write-Ahead Logging (`WAL` mode).

### `requirements.txt`
```text
PyQt6>=6.5.0
```

---

## 3. Storage Hierarchy & XDG Compliance
All persistent state must follow the XDG Base Directory specification:
- **Data & Database:** `${XDG_DATA_HOME:-$HOME/.local/share}/mint_tasks/`
- **Configuration & Preferences:** `${XDG_CONFIG_HOME:-$HOME/.config}/mint_tasks/`
- **Cache & Temp Logs:** `${XDG_CACHE_HOME:-$HOME/.cache}/mint_tasks/`
- **Desktop Launcher:** `$HOME/.local/share/applications/mint_tasks.desktop`

---

## 4. UI/UX & Responsive Layout Requirements
- **Responsive Architecture:** Built using adaptive layouts (`QVBoxLayout`, `QHBoxLayout`, `QSplitter`, `QScrollArea`) ensuring clean scaling from 400x500 (compact mobile-style panel) up to 4K desktop screens without text clipping or horizontal overflow.
- **Top Navigation Bar:**
  - **Tab 1: "Tasks"** (Active tasks and subtasks).
  - **Tab 2: "History"** (Completed task archive, restore actions, hard purge).
  - **Tab 3+: "Notes"** (Dynamic multi-tab document editor).
  - **Right Action Bar:** Theme switcher (Dark / Light toggle) and "Add Note" (`+`) action.
- **Visual Styling:**
  - Minimalist aesthetic inspired by Google Tasks: flat cards, subtle borders, 8px border-radius, clean typography.
  - **Dark Mode:** `#1e1e2e` background, `#2a2b3d` card surfaces, `#cdd6f4` primary text.
  - **Light Mode:** `#f8f9fa` background, `#ffffff` card surfaces, `#212529` primary text.
- **System Tray:** Minimize-to-tray icon (`QSystemTrayIcon`) to keep the reminder daemon running quietly in the background.

---

## 5. Functional Specifications

### 5.1. Tasks Module
- **Hierarchy:**
  - Top-level tasks containing: Checkbox, Title, Details/Notes field, Due Date, and Due Time.
  - Collapsible Subtasks nested under parent tasks, with independent completion states and due timestamps.
- **Scheduling & Reminders:**
  - Integrated `QDateTimeEdit` picker.
  - Background daemon thread checking due tasks every 30 seconds.
  - When the due timestamp arrives:
    - Triggers desktop notification via `notify-send` or DBus with task title and notes.
    - Emits a non-intrusive sound alert if available on system.
- **Actions:**
  - Complete task: strike-through visual feedback, automatically moves the record to the History tab.
  - Drag-and-drop or priority ordering (Starred / Urgent).

### 5.2. History & Permanent Purge Module
- Displays all completed tasks grouped by date completed.
- **Actions:**
  - **Restore:** Moves task and associated subtasks back into the active Tasks view.
  - **Delete Permanently (Hard Purge):** Strictly removes the task record and child subtasks from SQLite (`DELETE FROM tasks WHERE id = ?`).
  - **Clear All History:** Batch-purges all archived rows with a user confirmation prompt.
  - **Factory Reset:** Wipes the database files (`tasks.db`, `tasks.db-wal`, `tasks.db-shm`) and restores the app to an out-of-the-box empty state.

### 5.3. Multi-Tab Notes Module (Win11 Notepad Style)
- Dynamic tabs with `Ctrl+N` (New Tab) and `Ctrl+W` (Close Tab).
- Each tab hosts a clean `QPlainTextEdit` editor.
- **Status Bar:** Displays line count, character/word count, and current cursor position.
- **Unsaved Changes Indicator:** Prepends an asterisk (`*`) to the tab title when modified; prompts to save before closing.
- **Format Agnostic:** Allows Opening and Saving files in any plain text format supported on Linux (`.txt`, `.md`, `.py`, `.sh`, `.json`, `.yaml`, `.csv`, `.log`, or extensionless).

---

## 6. Linux Security & Hardening Directives
- **Least Privilege:** Do not require or invoke `sudo` anywhere. The entire lifecycle operates in standard user space.
- **POSIX Permission Masking:**
  - Directories (`~/.local/share/mint_tasks/`) must be explicitly created with permissions `0700` (`rwx------`).
  - Database files (`tasks.db`) must be initialized with `0600` (`rw-------`) so other users on the multi-user system cannot read task contents.
- **Injection Safety:**
  - All database queries MUST use SQLite parameter binding (`?` placeholders). String concatenation or formatting for SQL queries is strictly banned.
  - All notification or system calls must execute via `subprocess.run(["notify-send", ...], shell=False)`.
- **Path Sanitization:** User file operations in the Notes tab must validate paths to prevent directory traversal outside user permissions.

---

## 7. Project File Structure
```text
mint_tasks/
├── main.py                  # Application entry point, tray icon, main loop
├── database.py              # SQLite schemas, secure permissions, CRUD & purge
├── scheduler.py             # Background timer monitoring due alerts
├── theme.py                 # QSS stylesheets for Dark and Light modes
├── ui/
│   ├── __init__.py
│   ├── main_window.py       # Shell housing QTabWidget, header, tray handling
│   ├── tasks_tab.py         # Google Tasks clone: task cards, subtasks, pickers
│   ├── history_tab.py       # Completed tasks list with permanent delete & purge
│   └── notes_tab.py         # Tabbed text editor with open/save dialogs
├── requirements.txt         # Minimal PyQt6 dependency
├── mint_tasks.desktop       # Desktop entry for Linux Mint application menu
├── install.sh               # Local user-level setup script
└── uninstall.sh             # Complete data & binary purge script
```

---

## 8. Installation & Uninstallation Scripts

### `install.sh`
```bash
#!/usr/bin/env bash
set -e

APP_DIR="$HOME/.local/share/mint_tasks/app"
VENV_DIR="$HOME/.local/share/mint_tasks/venv"
DESKTOP_DIR="$HOME/.local/share/applications"

echo "Creating secure directories..."
mkdir -p "$APP_DIR"
mkdir -p "$HOME/.local/share/mint_tasks"
chmod 700 "$HOME/.local/share/mint_tasks"

echo "Setting up Python virtual environment..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r requirements.txt

echo "Copying application source files..."
cp -r ./* "$APP_DIR/"

echo "Installing desktop launcher..."
mkdir -p "$DESKTOP_DIR"
cat <<EOF> "$DESKTOP_DIR/mint_tasks.desktop"
[Desktop Entry]
Name=Mint Tasks
Comment=Minimalist Tasks & Notes for Linux Mint
Exec=$VENV_DIR/bin/python3 $APP_DIR/main.py
Icon=utilities-tasks
Terminal=false
Type=Application
Categories=Utility;Office;
EOF

update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
echo "Installation complete. Mint Tasks is now available in your application menu."
```

### `uninstall.sh` (Complete Purge)
```bash
#!/usr/bin/env bash
set -e

echo "Terminating any active Mint Tasks instances..."
pkill -f "mint_tasks/main.py" || true

echo "Completely purging application binaries, databases, and caches..."
rm -rf "$HOME/.local/share/mint_tasks"
rm -rf "$HOME/.config/mint_tasks"
rm -rf "$HOME/.cache/mint_tasks"

echo "Removing desktop entry..."
rm -f "$HOME/.local/share/applications/mint_tasks.desktop"
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo "Success: Mint Tasks, all SQLite records, configurations, and shortcuts have been permanently removed."
```

---

## 9. Antigravity Agent Execution Instructions
1. Initialize the directory structure and implement `database.py` first, ensuring `0600` permissions on file creation and proper SQLite `PRAGMA foreign_keys = ON;`.
2. Implement `ui/tasks_tab.py`, `ui/history_tab.py`, and `ui/notes_tab.py` with modular PyQt6 widgets.
3. Integrate the `scheduler.py` thread with `main_window.py` to trigger alerts reliably.
4. Verify window responsiveness at narrow widths (e.g., 380px) and broad widescreen dimensions (1920px+).
5. Verify that clicking "Delete Permanently" in History performs an immediate SQLite `DELETE` rather than a soft flag.
6. Make `install.sh` and `uninstall.sh` executable (`chmod +x`).