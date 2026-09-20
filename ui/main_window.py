"""Main window container for Mint Tasks.

Houses the top navigation bar (Tasks, History, Notes), Theme toggle (Dark/Light),
Add Note shortcut, System Tray integration, and window state persistence.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QCloseEvent, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QStyle,
    QSystemTrayIcon,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from database import DatabaseManager
from theme import get_stylesheet, load_config, save_config
from ui.history_tab import HistoryTab
from ui.notes_tab import NotesWorkspaceTab
from ui.tasks_tab import TasksTab


def get_app_icon() -> QIcon:
    """Find and return application QIcon from local paths or theme fallback."""
    current_dir = Path(__file__).resolve().parent
    candidates = [
        current_dir.parent / "mint_tasks_icon.svg",
        current_dir.parent / "Task-svg.svg",
        Path.home() / ".local" / "share" / "icons" / "hicolor" / "scalable" / "apps" / "mint-tasks.svg",
        Path.home() / ".local" / "share" / "mint_tasks" / "app" / "mint_tasks_icon.svg",
        Path.home() / ".local" / "share" / "mint_tasks" / "app" / "Task-svg.svg",
        current_dir / "mint_tasks_icon.svg",
    ]
    for p in candidates:
        if p.exists():
            icon = QIcon(str(p))
            if not icon.isNull():
                return icon
    return QIcon.fromTheme("utilities-tasks")


class MainWindow(QMainWindow):
    """Main Application Window."""

    def __init__(self, db: DatabaseManager) -> None:
        super().__init__()
        self.db = db
        self.config = load_config()
        self.current_theme = self.config.get("theme", "dark")

        self.setWindowTitle("Mint Tasks")
        self.setMinimumSize(380, 480)
        self.resize(
            self.config.get("window_width", 850),
            self.config.get("window_height", 650),
        )

        app_icon = get_app_icon()
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        self.init_ui()
        self.init_tray()
        self.apply_current_theme()

    def init_ui(self) -> None:
        # Central widget
        self.central_widget = QWidget()
        self.central_widget.setObjectName("centralWidget")
        self.setCentralWidget(self.central_widget)

        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header Frame
        header = QFrame()
        header.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 6, 12, 6)
        header_layout.setSpacing(10)

        # App Brand
        app_title = QLabel("🌿 Mint Tasks")
        app_title.setObjectName("appTitle")
        header_layout.addWidget(app_title)

        header_layout.addStretch()

        # Quick "Add Note" Button in header
        self.header_new_note_btn = QPushButton("📝 +Note")
        self.header_new_note_btn.setToolTip("Quickly create a new note")
        self.header_new_note_btn.clicked.connect(self._on_quick_new_note)
        header_layout.addWidget(self.header_new_note_btn)

        # Theme Switcher Button
        self.theme_btn = QPushButton()
        self.theme_btn.setObjectName("iconButton")
        self._update_theme_btn_text()
        self.theme_btn.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_btn)

        main_layout.addWidget(header)

        # Navigation Tabs
        self.nav_tabs = QTabWidget()
        self.nav_tabs.setDocumentMode(True)

        # Tab 1: Tasks
        self.tasks_tab = TasksTab(self.db, self)
        self.nav_tabs.addTab(self.tasks_tab, "Tasks")

        # Tab 2: History
        self.history_tab = HistoryTab(self.db, self)
        self.nav_tabs.addTab(self.history_tab, "History")

        # Tab 3: Notes
        self.notes_tab = NotesWorkspaceTab(self)
        self.nav_tabs.addTab(self.notes_tab, "Notes")

        # Connect signals between tabs
        self.tasks_tab.tasks_changed.connect(self.history_tab.refresh_history)
        self.history_tab.history_changed.connect(self.tasks_tab.refresh_tasks)
        self.history_tab.factory_reset_triggered.connect(self._on_factory_reset)

        main_layout.addWidget(self.nav_tabs)

    def init_tray(self) -> None:
        """Initialize system tray icon and context menu."""
        self.tray_icon = QSystemTrayIcon(self)

        app_icon = get_app_icon()
        if not app_icon.isNull():
            self.tray_icon.setIcon(app_icon)
            self.setWindowIcon(app_icon)
        else:
            standard_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
            self.tray_icon.setIcon(standard_icon)
            self.setWindowIcon(standard_icon)

        # Tray Menu
        tray_menu = QMenu()

        show_action = QAction("Show Mint Tasks", self)
        show_action.triggered.connect(self.show_and_activate)
        tray_menu.addAction(show_action)

        new_task_action = QAction("New Task", self)
        new_task_action.triggered.connect(self._on_tray_new_task)
        tray_menu.addAction(new_task_action)

        new_note_action = QAction("New Note", self)
        new_note_action.triggered.connect(self._on_quick_new_note)
        tray_menu.addAction(new_note_action)

        tray_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.force_quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def show_and_activate(self) -> None:
        """Restore and bring window to front."""
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            if self.isVisible() and not self.isMinimized():
                self.hide()
            else:
                self.show_and_activate()

    def _on_tray_new_task(self) -> None:
        self.show_and_activate()
        self.nav_tabs.setCurrentIndex(0)
        self.tasks_tab.quick_title_input.setFocus()

    def _on_quick_new_note(self) -> None:
        self.show_and_activate()
        self.nav_tabs.setCurrentIndex(2)
        self.notes_tab.add_new_note()

    def _on_factory_reset(self) -> None:
        self.tasks_tab.refresh_tasks()
        self.history_tab.refresh_history()

    def _update_theme_btn_text(self) -> None:
        if self.current_theme == "dark":
            self.theme_btn.setText("☀️ Light")
            self.theme_btn.setToolTip("Switch to Light Mode")
        else:
            self.theme_btn.setText("🌙 Dark")
            self.theme_btn.setToolTip("Switch to Dark Mode")

    def toggle_theme(self) -> None:
        """Toggle between Dark and Light modes and save preference."""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self._update_theme_btn_text()
        self.config["theme"] = self.current_theme
        save_config(self.config)
        self.apply_current_theme()

    def apply_current_theme(self) -> None:
        """Apply QSS stylesheet to the application."""
        sheet = get_stylesheet(self.current_theme)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(sheet)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event (prompt unsaved notes and optionally minimize to tray)."""
        if not self.notes_tab.check_all_saved_before_exit():
            event.ignore()
            return

        # Save window size
        self.config["window_width"] = self.width()
        self.config["window_height"] = self.height()
        save_config(self.config)

        # Minimize to tray if enabled
        if self.config.get("minimize_to_tray", True) and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Mint Tasks",
                "Mint Tasks is running in background tray.",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )
        else:
            event.accept()

    def force_quit(self) -> None:
        """Quit application completely."""
        if not self.notes_tab.check_all_saved_before_exit():
            return
        self.config["window_width"] = self.width()
        self.config["window_height"] = self.height()
        save_config(self.config)
        QApplication.quit()
