#!/usr/bin/env python3
"""Main entry point for Mint Tasks application.

Initializes database, starts background notification scheduler,
creates PyQt6 application with High-DPI support, sets application icon, and launches main window.
"""

from __future__ import annotations

import os
import signal
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from database import DatabaseManager
from scheduler import NotificationScheduler
from ui.main_window import MainWindow, get_app_icon


def main() -> int:
    # Allow clean Ctrl+C termination from terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Enable High-DPI scaling attributes where applicable
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("Mint Tasks")
    app.setApplicationDisplayName("Mint Tasks")
    app.setOrganizationName("LinuxMint")
    app.setQuitOnLastWindowClosed(False)

    # Set Application Icon
    app_icon = get_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    # Initialize Database with secure permissions
    db = DatabaseManager()

    # Create Main Window
    window = MainWindow(db)

    # Set Window Icon explicitly
    if not app_icon.isNull():
        window.setWindowIcon(app_icon)

    # Callback when tasks become due to refresh active task list if visible
    def on_due_tasks_callback(due_tasks: list) -> None:
        try:
            window.tasks_tab.refresh_tasks()
        except Exception:
            pass

    # Start Background Notification Scheduler
    scheduler = NotificationScheduler(db, interval_seconds=30, on_due_callback=on_due_tasks_callback)
    scheduler.start()

    # Show window
    window.show()

    # Run event loop
    ret = app.exec()

    # Cleanup background thread
    scheduler.stop()
    return ret


if __name__ == "__main__":
    sys.exit(main())
