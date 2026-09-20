"""History tab module — Modern Completed Tasks Archive.

Floating card layout, date-grouped sections, Restore & Hard Purge actions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from database import DatabaseManager
from theme import load_config


def _make_shadow(theme: str = "dark") -> QGraphicsDropShadowEffect:
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(14)
    shadow.setOffset(0, 3)
    shadow.setColor(QColor(0, 0, 0, 80 if theme == "dark" else 30))
    return shadow


class CompletedTaskCard(QFrame):
    """Floating card for a completed task in history."""

    restored = pyqtSignal(int)
    deleted_permanently = pyqtSignal(int)

    def __init__(
        self,
        task_data: Dict[str, Any],
        db: DatabaseManager,
        theme: str = "dark",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.task_data = task_data
        self.task_id = task_data["id"]
        self.db = db
        self.setObjectName("taskCard")
        self.setGraphicsEffect(_make_shadow(theme))
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 11, 14, 11)
        layout.setSpacing(6)

        # Top row: title + badge + restore + purge
        top = QHBoxLayout()
        top.setSpacing(8)

        self.title_label = QLabel(self.task_data.get("title", ""))
        font = self.title_label.font()
        font.setStrikeOut(True)
        self.title_label.setFont(font)
        self.title_label.setObjectName("taskTitleDone")
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top.addWidget(self.title_label)

        # Completed-at badge
        completed_at = self.task_data.get("completed_at", "")
        if completed_at:
            try:
                dt = datetime.fromisoformat(completed_at)
                time_str = dt.strftime("%b %d, %H:%M")
            except Exception:
                time_str = completed_at[:16]
            badge = QLabel(f"✓  {time_str}")
            badge.setObjectName("badgeUpcoming")
            top.addWidget(badge)

        # Restore
        restore_btn = QPushButton("↩  Restore")
        restore_btn.setFixedHeight(30)
        restore_btn.clicked.connect(self._on_restore)
        top.addWidget(restore_btn)

        # Hard Purge
        purge_btn = QPushButton("🗑  Purge")
        purge_btn.setObjectName("dangerBtn")
        purge_btn.setFixedHeight(30)
        purge_btn.setToolTip("Permanently DELETE from SQLite (cannot be undone)")
        purge_btn.clicked.connect(self._on_permanent_delete)
        top.addWidget(purge_btn)

        layout.addLayout(top)

        # Notes snippet
        notes = self.task_data.get("notes", "").strip()
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setObjectName("mutedLabel")
            notes_lbl.setWordWrap(True)
            notes_lbl.setContentsMargins(8, 0, 0, 0)
            layout.addWidget(notes_lbl)

        # Subtasks summary
        subtasks = self.task_data.get("subtasks", [])
        if subtasks:
            titles = ", ".join(s.get("title", "") for s in subtasks[:4])
            if len(subtasks) > 4:
                titles += f" +{len(subtasks) - 4} more"
            sub_lbl = QLabel(f"Subtasks: {titles}")
            sub_lbl.setObjectName("mutedLabel")
            sub_lbl.setWordWrap(True)
            sub_lbl.setContentsMargins(8, 0, 0, 0)
            layout.addWidget(sub_lbl)

    def _on_restore(self) -> None:
        self.db.restore_task(self.task_id)
        self.restored.emit(self.task_id)

    def _on_permanent_delete(self) -> None:
        confirm = QMessageBox.question(
            self,
            "Permanent Hard Purge",
            f"Permanently DELETE '{self.task_data.get('title')}' from SQLite?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.delete_task_permanently(self.task_id)
            self.deleted_permanently.emit(self.task_id)


class HistoryTab(QWidget):
    """History view: completed tasks grouped by date with batch actions."""

    history_changed = pyqtSignal()
    factory_reset_triggered = pyqtSignal()

    def __init__(self, db: DatabaseManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.db = db
        self.theme = load_config().get("theme", "dark")
        self.init_ui()
        self.refresh_history()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Top Action Bar ───────────────────────────────────────────────────
        action_bar = QFrame()
        action_bar.setObjectName("addTaskBar")
        action_bar.setContentsMargins(0, 0, 0, 0)
        action_bar.setFixedHeight(52)
        bar_layout = QHBoxLayout(action_bar)
        bar_layout.setContentsMargins(14, 0, 14, 0)
        bar_layout.setSpacing(10)

        self.count_label = QLabel("Completed Tasks")
        self.count_label.setObjectName("taskTitle")
        bar_layout.addWidget(self.count_label)
        bar_layout.addStretch()

        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setObjectName("dangerBtn")
        self.clear_btn.setFixedHeight(30)
        self.clear_btn.clicked.connect(self._clear_all_history)
        bar_layout.addWidget(self.clear_btn)

        self.reset_btn = QPushButton("Factory Reset")
        self.reset_btn.setObjectName("dangerBtn")
        self.reset_btn.setFixedHeight(30)
        self.reset_btn.clicked.connect(self._factory_reset)
        bar_layout.addWidget(self.reset_btn)

        layout.addWidget(action_bar)
        layout.addSpacing(4)

        # ── Scrollable history list ──────────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.list_widget = QWidget()
        self.list_widget.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 8, 0, 16)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch()

        self.scroll.setWidget(self.list_widget)
        layout.addWidget(self.scroll, stretch=1)

    def refresh_history(self) -> None:
        self.theme = load_config().get("theme", "dark")

        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tasks = self.db.get_history_tasks()
        count = len(tasks)
        self.count_label.setText(f"Completed Tasks  ({count})")
        self.clear_btn.setEnabled(count > 0)

        if not tasks:
            empty = QLabel("No completed tasks in history.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setObjectName("mutedLabel")
            empty.setContentsMargins(0, 48, 0, 48)
            self.list_layout.addWidget(empty)
        else:
            today_str = datetime.now().strftime("%Y-%m-%d")
            grouped: Dict[str, List[Dict[str, Any]]] = {}

            for t in tasks:
                ca = t.get("completed_at", "")
                key = ca[:10] if ca else "Earlier"
                grouped.setdefault(key, []).append(t)

            for date_key, group in grouped.items():
                # Section header
                display = "Today" if date_key == today_str else date_key
                hdr = QLabel(display.upper())
                hdr.setObjectName("sectionHeader")
                hdr.setContentsMargins(14, 10, 0, 4)
                self.list_layout.addWidget(hdr)

                for t in group:
                    card = CompletedTaskCard(t, self.db, self.theme, self)
                    card.restored.connect(self._on_restored)
                    card.deleted_permanently.connect(self._on_purged)
                    self.list_layout.addWidget(card)

        self.list_layout.addStretch()

    def _on_restored(self, task_id: int) -> None:
        self.refresh_history()
        self.history_changed.emit()

    def _on_purged(self, task_id: int) -> None:
        self.refresh_history()
        self.history_changed.emit()

    def _clear_all_history(self) -> None:
        confirm = QMessageBox.question(
            self,
            "Clear All History",
            "Permanently delete all completed tasks? This hard purge cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.clear_history()
            self.refresh_history()
            self.history_changed.emit()

    def _factory_reset(self) -> None:
        confirm = QMessageBox.warning(
            self,
            "Factory Reset",
            "Wipe ALL database files and erase every task, subtask, and history record?\n\nThis is irreversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.factory_reset()
            self.refresh_history()
            self.factory_reset_triggered.emit()
            self.history_changed.emit()
            QMessageBox.information(self, "Reset Complete", "Database has been reset to empty state.")
