"""Main window container for Mint Tasks — Modern Vertical Sidebar Layout.

Replaces the horizontal QTabWidget with a Material Design 3-inspired
vertical sidebar navigation with animated transitions between views.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QSize,
    Qt,
    QTimer,
)
from PyQt6.QtGui import QAction, QCloseEvent, QColor, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from database import DatabaseManager
from theme import DarkPalette, LightPalette, get_stylesheet, load_config, save_config
from ui.history_tab import HistoryTab
from ui.notes_tab import NotesWorkspaceTab
from ui.tasks_tab import TasksTab


def get_app_icon() -> QIcon:
    """Find and return application QIcon from local and system paths."""
    current_dir = Path(__file__).resolve().parent
    candidates = [
        current_dir.parent / "mint_tasks_icon.svg",
        current_dir.parent / "Task-svg.svg",
        Path("/usr/share/icons/hicolor/scalable/apps/mint-tasks.svg"),
        Path("/opt/mint_tasks/app/mint_tasks_icon.svg"),
        Path.home() / ".local" / "share" / "icons" / "hicolor" / "scalable" / "apps" / "mint-tasks.svg",
        Path.home() / ".local" / "share" / "mint_tasks" / "app" / "mint_tasks_icon.svg",
    ]
    for p in candidates:
        if p.exists():
            icon = QIcon(str(p))
            if not icon.isNull():
                return icon
    return QIcon.fromTheme("utilities-tasks")


class NavButton(QPushButton):
    """Sidebar navigation button with active-state styling."""

    def __init__(self, label: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(label, parent)
        self.setProperty("class", "navButton")
        self.setCheckable(False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(42)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_active(self, active: bool) -> None:
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


class SidebarWidget(QWidget):
    """Left sidebar containing navigation links, logo, and theme toggle."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("sidebarWidget")
        self.setFixedWidth(210)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(0)

        # App Logo / Name
        logo = QLabel("🌿 Mint Tasks")
        logo.setObjectName("appLogoLabel")
        logo.setContentsMargins(16, 20, 16, 12)
        layout.addWidget(logo)

        # Thin separator
        sep = QFrame()
        sep.setObjectName("hSeparator")
        sep.setFixedHeight(1)
        sep.setContentsMargins(12, 0, 12, 0)
        layout.addWidget(sep)

        layout.addSpacing(8)

        # Navigation Section Label
        nav_lbl = QLabel("NAVIGATION")
        nav_lbl.setObjectName("sectionHeader")
        nav_lbl.setContentsMargins(20, 8, 0, 4)
        layout.addWidget(nav_lbl)

        # Nav Buttons
        self.btn_tasks = NavButton("  ✓  Tasks", self)
        self.btn_history = NavButton("  🕘  History", self)
        self.btn_notes = NavButton("  📝  Notes", self)

        for btn in (self.btn_tasks, self.btn_history, self.btn_notes):
            layout.addWidget(btn)

        layout.addStretch()

        # Bottom separator
        sep2 = QFrame()
        sep2.setObjectName("hSeparator")
        sep2.setFixedHeight(1)
        layout.addWidget(sep2)
        layout.addSpacing(8)

        # Theme Toggle
        self.theme_btn = QPushButton()
        self.theme_btn.setObjectName("themeToggleBtn")
        self.theme_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.theme_btn.setMinimumHeight(38)
        layout.addWidget(self.theme_btn)

        # Set initial active
        self.btn_tasks.set_active(True)

    def set_active_index(self, index: int) -> None:
        buttons = [self.btn_tasks, self.btn_history, self.btn_notes]
        for i, btn in enumerate(buttons):
            btn.set_active(i == index)


class MainWindow(QMainWindow):
    """Main Application Window with vertical sidebar navigation."""

    def __init__(self, db: DatabaseManager) -> None:
        super().__init__()
        self.db = db
        self.config = load_config()
        self.current_theme = self.config.get("theme", "dark")
        self._current_index = 0

        self.setWindowTitle("Mint Tasks")
        self.setMinimumSize(620, 520)
        self.resize(
            self.config.get("window_width", 960),
            self.config.get("window_height", 680),
        )

        app_icon = get_app_icon()
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        self.init_ui()
        self.init_tray()
        self.apply_current_theme()

    def init_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Sidebar ─────────────────────────────────────────────────────────
        self.sidebar = SidebarWidget(self)
        root_layout.addWidget(self.sidebar)

        # Vertical separator between sidebar and content
        vsep = QFrame()
        vsep.setObjectName("vSeparator")
        vsep.setFixedWidth(1)
        root_layout.addWidget(vsep)

        # ── Content Stack ────────────────────────────────────────────────────
        content_outer = QWidget()
        content_outer.setObjectName("contentStack")
        content_layout = QVBoxLayout(content_outer)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Content header bar (Page title + quick actions)
        self.header_bar = self._build_header_bar()
        content_layout.addWidget(self.header_bar)

        # Stacked pages
        self.stack = QStackedWidget()
        self.stack.setObjectName("contentStack")

        self.tasks_tab = TasksTab(self.db, self)
        self.history_tab = HistoryTab(self.db, self)
        self.notes_tab = NotesWorkspaceTab(self)

        self.stack.addWidget(self.tasks_tab)    # index 0
        self.stack.addWidget(self.history_tab)  # index 1
        self.stack.addWidget(self.notes_tab)    # index 2

        content_layout.addWidget(self.stack)
        root_layout.addWidget(content_outer, stretch=1)

        # Fade-out/in opacity effect for page transitions
        self._opacity_effect = QGraphicsOpacityEffect(self.stack)
        self.stack.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(1.0)
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._fade_anim.setDuration(200)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # ── Wire sidebar buttons ─────────────────────────────────────────────
        self.sidebar.btn_tasks.clicked.connect(lambda: self.navigate_to(0))
        self.sidebar.btn_history.clicked.connect(lambda: self.navigate_to(1))
        self.sidebar.btn_notes.clicked.connect(lambda: self.navigate_to(2))
        self.sidebar.theme_btn.clicked.connect(self.toggle_theme)

        # ── Cross-tab signals ─────────────────────────────────────────────
        self.tasks_tab.tasks_changed.connect(self.history_tab.refresh_history)
        self.history_tab.history_changed.connect(self.tasks_tab.refresh_tasks)
        self.history_tab.factory_reset_triggered.connect(self._on_factory_reset)

        self._update_theme_btn_text()
        self._update_header("Tasks")

    def _build_header_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("addTaskBar")
        bar.setFixedHeight(52)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 12, 0)
        layout.setSpacing(10)

        self.page_title_label = QLabel("Tasks")
        self.page_title_label.setStyleSheet(
            "font-size: 16px; font-weight: 700;"
        )
        layout.addWidget(self.page_title_label)
        layout.addStretch()

        # Quick Add Note button shown only when Notes is active
        self.quick_note_btn = QPushButton("+ Note")
        self.quick_note_btn.setObjectName("primaryBtn")
        self.quick_note_btn.setFixedHeight(32)
        self.quick_note_btn.clicked.connect(self._on_quick_new_note)
        self.quick_note_btn.hide()
        layout.addWidget(self.quick_note_btn)

        return bar

    def _update_header(self, title: str) -> None:
        self.page_title_label.setText(title)
        self.quick_note_btn.setVisible(title == "Notes")

    def navigate_to(self, index: int) -> None:
        """Fade-out → switch page → fade-in."""
        if index == self._current_index:
            return

        def do_switch() -> None:
            self.stack.setCurrentIndex(index)
            self.sidebar.set_active_index(index)
            self._current_index = index
            titles = ["Tasks", "History", "Notes"]
            self._update_header(titles[index])
            # Fade in
            self._fade_anim.setStartValue(0.0)
            self._fade_anim.setEndValue(1.0)
            self._fade_anim.start()

        # Fade out first
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.start()
        QTimer.singleShot(200, do_switch)

    def init_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self)
        app_icon = get_app_icon()
        if not app_icon.isNull():
            self.tray_icon.setIcon(app_icon)
            self.setWindowIcon(app_icon)
        else:
            std = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
            self.tray_icon.setIcon(std)
            self.setWindowIcon(std)

        tray_menu = QMenu()
        show_act = QAction("Show Mint Tasks", self)
        show_act.triggered.connect(self.show_and_activate)
        tray_menu.addAction(show_act)

        new_task_act = QAction("New Task", self)
        new_task_act.triggered.connect(self._on_tray_new_task)
        tray_menu.addAction(new_task_act)

        new_note_act = QAction("New Note", self)
        new_note_act.triggered.connect(self._on_quick_new_note)
        tray_menu.addAction(new_note_act)

        tray_menu.addSeparator()

        quit_act = QAction("Quit", self)
        quit_act.triggered.connect(self.force_quit)
        tray_menu.addAction(quit_act)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def show_and_activate(self) -> None:
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
        self.navigate_to(0)
        QTimer.singleShot(250, self.tasks_tab.quick_title_input.setFocus)

    def _on_quick_new_note(self) -> None:
        self.show_and_activate()
        self.navigate_to(2)
        QTimer.singleShot(250, self.notes_tab.add_new_note)

    def _on_factory_reset(self) -> None:
        self.tasks_tab.refresh_tasks()
        self.history_tab.refresh_history()

    def _update_theme_btn_text(self) -> None:
        if self.current_theme == "dark":
            self.sidebar.theme_btn.setText("  ☀  Light Mode")
        else:
            self.sidebar.theme_btn.setText("  🌙  Dark Mode")

    def toggle_theme(self) -> None:
        """Fade out → change theme → fade in."""
        def do_switch() -> None:
            self.current_theme = "light" if self.current_theme == "dark" else "dark"
            self._update_theme_btn_text()
            self.config["theme"] = self.current_theme
            save_config(self.config)
            self.apply_current_theme()
            # Fade in
            fade_in = QPropertyAnimation(self._opacity_effect, b"opacity", self)
            fade_in.setDuration(250)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.Type.InOutCubic)
            fade_in.start()

        # Fade out
        fade_out = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        fade_out.setDuration(150)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        fade_out.start()
        QTimer.singleShot(160, do_switch)

    def apply_current_theme(self) -> None:
        sheet = get_stylesheet(self.current_theme)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(sheet)

    def closeEvent(self, event: QCloseEvent) -> None:
        if not self.notes_tab.check_all_saved_before_exit():
            event.ignore()
            return
        self.config["window_width"] = self.width()
        self.config["window_height"] = self.height()
        save_config(self.config)
        if self.config.get("minimize_to_tray", True) and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Mint Tasks",
                "Running in background tray.",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )
        else:
            event.accept()

    def force_quit(self) -> None:
        if not self.notes_tab.check_all_saved_before_exit():
            return
        self.config["window_width"] = self.width()
        self.config["window_height"] = self.height()
        save_config(self.config)
        QApplication.quit()
