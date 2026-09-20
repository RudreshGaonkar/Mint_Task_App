"""History tab module for Mint Tasks.

Displays archived/completed tasks grouped by completion date.
Provides Restore, Hard Purge (Permanent Delete), Clear All History, and Factory Reset actions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
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


class CompletedTaskCard(QFrame):
    """Card widget representing a completed task in the history archive."""

    restored = pyqtSignal(int)
    deleted_permanently = pyqtSignal(int)

    def __init__(
        self,
        task_data: Dict[str, Any],
        db: DatabaseManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.task_data = task_data
        self.task_id = task_data["id"]
        self.db = db
        self.setProperty("class", "taskCard")
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Header Row: Strike-through Title, Completed Badge, Restore & Purge buttons
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        # Title with strike-through
        self.title_label = QLabel(self.task_data.get("title", ""))
        font = QFont()
        font.setPointSize(11)
        font.setStrikeOut(True)
        self.title_label.setFont(font)
        self.title_label.setStyleSheet("color: gray;")
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        header_row.addWidget(self.title_label)

        # Completed time badge
        completed_at = self.task_data.get("completed_at", "")
        if completed_at:
            try:
                dt = datetime.fromisoformat(completed_at)
                time_str = dt.strftime("%b %d, %H:%M")
            except Exception:
                time_str = completed_at[:16]
            time_badge = QLabel(f"✓ {time_str}")
            time_badge.setObjectName("badgeUpcoming")
            header_row.addWidget(time_badge)

        # Restore button
        restore_btn = QPushButton("↩ Restore")
        restore_btn.setToolTip("Restore task back to active list")
        restore_btn.clicked.connect(self._on_restore)
        header_row.addWidget(restore_btn)

        # Permanent Delete (Hard Purge) button
        delete_btn = QPushButton("🗑 Purge")
        delete_btn.setObjectName("dangerButton")
        delete_btn.setToolTip("Permanently delete from database (hard purge)")
        delete_btn.clicked.connect(self._on_permanent_delete)
        header_row.addWidget(delete_btn)

        layout.addLayout(header_row)

        # Notes
        notes = self.task_data.get("notes", "").strip()
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setObjectName("mutedText")
            notes_lbl.setWordWrap(True)
            notes_lbl.setContentsMargins(12, 0, 0, 0)
            layout.addWidget(notes_lbl)

        # Subtasks summary if any
        subtasks = self.task_data.get("subtasks", [])
        if subtasks:
            sub_summary = QLabel(f"Subtasks ({len(subtasks)} completed): " + ", ".join(s.get("title", "") for s in subtasks))
            sub_summary.setObjectName("mutedText")
            sub_summary.setStyleSheet("font-size: 11px; color: gray;")
            sub_summary.setWordWrap(True)
            sub_summary.setContentsMargins(12, 2, 0, 0)
            layout.addWidget(sub_summary)

    def _on_restore(self) -> None:
        self.db.restore_task(self.task_id)
        self.restored.emit(self.task_id)

    def _on_permanent_delete(self) -> None:
        # Prompt for confirmation
        confirm = QMessageBox.question(
            self,
            "Permanent Hard Purge",
            f"Are you sure you want to permanently delete '{self.task_data.get('title')}'?\nThis will completely purge the record from SQLite and cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.delete_task_permanently(self.task_id)
            self.deleted_permanently.emit(self.task_id)


class HistoryTab(QWidget):
    """History tab containing completed tasks, grouping, Clear All History, and Factory Reset."""

    history_changed = pyqtSignal()
    factory_reset_triggered = pyqtSignal()

    def __init__(self, db: DatabaseManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.refresh_history()

    def init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Top Action Bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        self.summary_label = QLabel("Completed Tasks")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.summary_label.setFont(font)
        top_bar.addWidget(self.summary_label)

        top_bar.addStretch()

        # Clear All History button
        self.clear_all_btn = QPushButton("Clear All History")
        self.clear_all_btn.setObjectName("dangerButton")
        self.clear_all_btn.setToolTip("Batch purge all completed tasks")
        self.clear_all_btn.clicked.connect(self._clear_all_history)
        top_bar.addWidget(self.clear_all_btn)

        # Factory Reset button
        self.factory_reset_btn = QPushButton("Factory Reset")
        self.factory_reset_btn.setObjectName("dangerButton")
        self.factory_reset_btn.setToolTip("Wipe database files and reset to empty state")
        self.factory_reset_btn.clicked.connect(self._factory_reset)
        top_bar.addWidget(self.factory_reset_btn)

        main_layout.addLayout(top_bar)

        # Scroll Area for history tasks
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.history_container = QWidget()
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setContentsMargins(0, 4, 0, 4)
        self.history_layout.setSpacing(8)
        self.history_layout.addStretch()

        self.scroll.setWidget(self.history_container)
        main_layout.addWidget(self.scroll)

    def refresh_history(self) -> None:
        """Reload completed tasks from database and group them by date."""
        while self.history_layout.count():
            item = self.history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tasks = self.db.get_history_tasks()
        count = len(tasks)
        self.summary_label.setText(f"Completed Tasks ({count})")
        self.clear_all_btn.setEnabled(count > 0)

        if not tasks:
            empty_lbl = QLabel("No completed tasks in history.")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setObjectName("mutedText")
            empty_lbl.setContentsMargins(0, 40, 0, 40)
            self.history_layout.addWidget(empty_lbl)
        else:
            # Group tasks by date
            today_str = datetime.now().strftime("%Y-%m-%d")
            grouped: Dict[str, List[Dict[str, Any]]] = {}

            for t in tasks:
                completed_at = t.get("completed_at")
                if completed_at:
                    date_key = completed_at[:10]
                else:
                    date_key = "Earlier"
                grouped.setdefault(date_key, []).append(t)

            for date_key, task_group in grouped.items():
                # Section header
                header_title = "Today" if date_key == today_str else date_key
                section_lbl = QLabel(header_title)
                section_font = QFont()
                section_font.setBold(True)
                section_lbl.setFont(section_font)
                section_lbl.setObjectName("mutedText")
                section_lbl.setContentsMargins(4, 8, 4, 2)
                self.history_layout.addWidget(section_lbl)

                for t in task_group:
                    card = CompletedTaskCard(t, self.db, self)
                    card.restored.connect(self._on_item_restored)
                    card.deleted_permanently.connect(self._on_item_purged)
                    self.history_layout.addWidget(card)

        self.history_layout.addStretch()

    def _on_item_restored(self, task_id: int) -> None:
        self.refresh_history()
        self.history_changed.emit()

    def _on_item_purged(self, task_id: int) -> None:
        self.refresh_history()
        self.history_changed.emit()

    def _clear_all_history(self) -> None:
        confirm = QMessageBox.question(
            self,
            "Clear All History",
            "Are you sure you want to permanently delete all completed tasks?\nThis hard purge cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.clear_history()
            self.refresh_history()
            self.history_changed.emit()

    def _factory_reset(self) -> None:
        confirm = QMessageBox.warning(
            self,
            "Factory Reset Warning",
            "Factory reset will wipe all database files and completely erase all tasks, subtasks, and history.\n\nAre you absolutely sure you want to proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.factory_reset()
            self.refresh_history()
            self.factory_reset_triggered.emit()
            self.history_changed.emit()
            QMessageBox.information(
                self,
                "Reset Complete",
                "Application database has been reset to an empty out-of-the-box state.",
            )
