"""Tasks tab module for Mint Tasks.

Implements Google Tasks-style interface: active task cards, inline task creator,
collapsible subtasks, date/time pickers, star/priority toggles, and strike-through completion.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from PyQt6.QtCore import QDate, QTime, Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from database import DatabaseManager


class SubtaskWidget(QFrame):
    """Widget representing an individual subtask."""

    subtask_toggled = pyqtSignal(int, bool)
    subtask_deleted = pyqtSignal(int)

    def __init__(self, subtask_data: Dict[str, Any], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.subtask_data = subtask_data
        self.subtask_id = subtask_data["id"]
        self.setProperty("class", "subtaskCard")
        self.init_ui()

    def init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(bool(self.subtask_data.get("is_completed", 0)))
        self.checkbox.toggled.connect(self._on_toggled)
        layout.addWidget(self.checkbox)

        # Title
        self.title_label = QLabel(self.subtask_data.get("title", ""))
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._update_text_style()
        layout.addWidget(self.title_label)

        # Delete button
        self.del_btn = QPushButton("✕")
        self.del_btn.setObjectName("iconButton")
        self.del_btn.setToolTip("Delete subtask")
        self.del_btn.setFixedSize(22, 22)
        self.del_btn.clicked.connect(lambda: self.subtask_deleted.emit(self.subtask_id))
        layout.addWidget(self.del_btn)

    def _update_text_style(self) -> None:
        font = self.title_label.font()
        font.setStrikeOut(self.checkbox.isChecked())
        self.title_label.setFont(font)
        if self.checkbox.isChecked():
            self.title_label.setStyleSheet("color: gray;")
        else:
            self.title_label.setStyleSheet("")

    def _on_toggled(self, checked: bool) -> None:
        self._update_text_style()
        self.subtask_toggled.emit(self.subtask_id, checked)


class TaskCardWidget(QFrame):
    """Card widget representing a top-level task with nested subtasks."""

    task_completed = pyqtSignal(int)
    task_updated = pyqtSignal()
    task_deleted = pyqtSignal(int)

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
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 10, 12, 10)
        self.main_layout.setSpacing(6)

        # Top row: Checkbox, Title, Due Badge, Star, Actions Menu
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setToolTip("Mark completed")
        self.checkbox.toggled.connect(self._on_complete)
        top_row.addWidget(self.checkbox)

        # Star toggle button
        self.star_btn = QPushButton("★" if self.task_data.get("is_starred") else "☆")
        self.star_btn.setObjectName("starButton")
        self.star_btn.setProperty("starred", "true" if self.task_data.get("is_starred") else "false")
        self.star_btn.setFixedSize(26, 26)
        self.star_btn.setToolTip("Toggle star priority")
        self.star_btn.clicked.connect(self._toggle_star)
        top_row.addWidget(self.star_btn)

        # Title Label
        self.title_label = QLabel(self.task_data.get("title", ""))
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_row.addWidget(self.title_label)

        # Due Date Badge
        self._add_due_badge(top_row)

        # Edit button
        self.edit_btn = QPushButton("✎")
        self.edit_btn.setObjectName("iconButton")
        self.edit_btn.setFixedSize(26, 26)
        self.edit_btn.setToolTip("Edit task details")
        self.edit_btn.clicked.connect(self._open_edit_dialog)
        top_row.addWidget(self.edit_btn)

        # Delete button
        self.delete_btn = QPushButton("🗑")
        self.delete_btn.setObjectName("iconButton")
        self.delete_btn.setFixedSize(26, 26)
        self.delete_btn.setToolTip("Delete task permanently")
        self.delete_btn.clicked.connect(self._on_delete)
        top_row.addWidget(self.delete_btn)

        self.main_layout.addLayout(top_row)

        # Notes / Details section (if present)
        notes = self.task_data.get("notes", "").strip()
        if notes:
            self.notes_label = QLabel(notes)
            self.notes_label.setObjectName("mutedText")
            self.notes_label.setWordWrap(True)
            self.notes_label.setContentsMargins(34, 0, 0, 4)
            self.main_layout.addWidget(self.notes_label)

        # Subtasks container
        self.subtasks_container = QVBoxLayout()
        self.subtasks_container.setContentsMargins(18, 2, 0, 2)
        self.subtasks_container.setSpacing(4)
        self.main_layout.addLayout(self.subtasks_container)

        self._render_subtasks()

        # Add Subtask Inline Bar
        sub_input_layout = QHBoxLayout()
        sub_input_layout.setContentsMargins(28, 4, 0, 0)
        sub_input_layout.setSpacing(6)

        self.sub_input = QLineEdit()
        self.sub_input.setPlaceholderText("+ Add a subtask...")
        self.sub_input.returnPressed.connect(self._add_subtask)
        sub_input_layout.addWidget(self.sub_input)

        add_sub_btn = QPushButton("+")
        add_sub_btn.setFixedSize(28, 28)
        add_sub_btn.clicked.connect(self._add_subtask)
        sub_input_layout.addWidget(add_sub_btn)

        self.main_layout.addLayout(sub_input_layout)

    def _add_due_badge(self, layout: QHBoxLayout) -> None:
        due_date = self.task_data.get("due_date")
        due_time = self.task_data.get("due_time")
        if not due_date:
            return

        now_date_str = datetime.now().strftime("%Y-%m-%d")
        badge = QLabel()
        badge_text = due_date
        if due_time:
            badge_text += f" {due_time}"

        if due_date < now_date_str:
            badge.setObjectName("badgeOverdue")
            badge.setText(f"⚠ {badge_text}")
        elif due_date == now_date_str:
            badge.setObjectName("badgeToday")
            badge.setText(f"Today {due_time or ''}".strip())
        else:
            badge.setObjectName("badgeUpcoming")
            badge.setText(f"📅 {badge_text}")

        layout.addWidget(badge)

    def _render_subtasks(self) -> None:
        # Clear existing
        while self.subtasks_container.count():
            item = self.subtasks_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        subtasks = self.task_data.get("subtasks", [])
        for sub in subtasks:
            sub_widget = SubtaskWidget(sub, self)
            sub_widget.subtask_toggled.connect(self._on_subtask_toggled)
            sub_widget.subtask_deleted.connect(self._on_subtask_deleted)
            self.subtasks_container.addWidget(sub_widget)

    def _on_subtask_toggled(self, subtask_id: int, checked: bool) -> None:
        self.db.complete_subtask(subtask_id, checked)

    def _on_subtask_deleted(self, subtask_id: int) -> None:
        self.db.delete_task_permanently(subtask_id)
        # Refresh local data
        self.task_data["subtasks"] = self.db.get_subtasks(self.task_id)
        self._render_subtasks()

    def _add_subtask(self) -> None:
        text = self.sub_input.text().strip()
        if not text:
            return
        self.db.add_task(title=text, parent_id=self.task_id)
        self.sub_input.clear()
        self.task_data["subtasks"] = self.db.get_subtasks(self.task_id)
        self._render_subtasks()

    def _toggle_star(self) -> None:
        current = bool(self.task_data.get("is_starred", 0))
        new_state = not current
        self.db.update_task(self.task_id, is_starred=new_state)
        self.task_updated.emit()

    def _on_complete(self, checked: bool) -> None:
        if checked:
            font = self.title_label.font()
            font.setStrikeOut(True)
            self.title_label.setFont(font)
            self.db.complete_task(self.task_id, True)
            self.task_completed.emit(self.task_id)

    def _on_delete(self) -> None:
        confirm = QMessageBox.question(
            self,
            "Delete Task",
            f"Permanently delete '{self.task_data.get('title')}' and all subtasks?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.delete_task_permanently(self.task_id)
            self.task_deleted.emit(self.task_id)

    def _open_edit_dialog(self) -> None:
        dialog = TaskEditDialog(self.task_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title, notes, due_date, due_time = dialog.get_values()
            self.db.update_task(
                self.task_id,
                title=title,
                notes=notes,
                due_date=due_date,
                due_time=due_time,
            )
            self.task_updated.emit()


class TaskEditDialog(QDialog):
    """Dialog for editing task title, notes, and due date/time."""

    def __init__(self, task_data: Dict[str, Any], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.task_data = task_data
        self.setWindowTitle("Edit Task")
        self.setMinimumWidth(380)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Title
        layout.addWidget(QLabel("Title:"))
        self.title_edit = QLineEdit(self.task_data.get("title", ""))
        layout.addWidget(self.title_edit)

        # Notes
        layout.addWidget(QLabel("Details / Notes:"))
        self.notes_edit = QTextEdit(self.task_data.get("notes", ""))
        self.notes_edit.setMaximumHeight(90)
        layout.addWidget(self.notes_edit)

        # Due Date & Time
        due_row = QHBoxLayout()
        self.has_due_cb = QCheckBox("Set Due Date & Time")
        current_due_date = self.task_data.get("due_date")
        current_due_time = self.task_data.get("due_time")
        self.has_due_cb.setChecked(bool(current_due_date))
        due_row.addWidget(self.has_due_cb)
        layout.addLayout(due_row)

        picker_row = QHBoxLayout()
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        if current_due_date:
            try:
                d = QDate.fromString(current_due_date, "yyyy-MM-dd")
                self.date_picker.setDate(d)
            except Exception:
                self.date_picker.setDate(QDate.currentDate())
        else:
            self.date_picker.setDate(QDate.currentDate())

        self.time_picker = QTimeEdit()
        if current_due_time:
            try:
                t = QTime.fromString(current_due_time, "HH:mm")
                self.time_picker.setTime(t)
            except Exception:
                self.time_picker.setTime(QTime.currentTime())
        else:
            self.time_picker.setTime(QTime(12, 0))

        self.date_picker.setEnabled(self.has_due_cb.isChecked())
        self.time_picker.setEnabled(self.has_due_cb.isChecked())
        self.has_due_cb.toggled.connect(self.date_picker.setEnabled)
        self.has_due_cb.toggled.connect(self.time_picker.setEnabled)

        picker_row.addWidget(self.date_picker)
        picker_row.addWidget(self.time_picker)
        layout.addLayout(picker_row)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self) -> tuple[str, str, Optional[str], Optional[str]]:
        title = self.title_edit.text().strip()
        notes = self.notes_edit.toPlainText().strip()
        if self.has_due_cb.isChecked():
            due_date = self.date_picker.date().toString("yyyy-MM-dd")
            due_time = self.time_picker.time().toString("HH:mm")
        else:
            due_date = ""
            due_time = ""
        return title, notes, due_date, due_time


class TasksTab(QWidget):
    """Main Tasks Tab containing the quick add bar, task filter, and scrollable cards."""

    tasks_changed = pyqtSignal()

    def __init__(self, db: DatabaseManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.refresh_tasks()

    def init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Top Quick-Add Bar
        add_frame = QFrame()
        add_frame.setProperty("class", "taskCard")
        add_layout = QVBoxLayout(add_frame)
        add_layout.setContentsMargins(10, 10, 10, 10)
        add_layout.setSpacing(8)

        # Title & Add button row
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        self.quick_star_btn = QPushButton("☆")
        self.quick_star_btn.setObjectName("starButton")
        self.quick_star_btn.setFixedSize(26, 26)
        self.quick_star_btn.setToolTip("Mark task as starred")
        self.quick_star_btn.clicked.connect(self._toggle_quick_star)
        self.is_quick_starred = False
        title_row.addWidget(self.quick_star_btn)

        self.quick_title_input = QLineEdit()
        self.quick_title_input.setPlaceholderText("Add a task...")
        self.quick_title_input.returnPressed.connect(self.add_task_action)
        title_row.addWidget(self.quick_title_input)

        self.add_btn = QPushButton("Add")
        self.add_btn.setObjectName("accentButton")
        self.add_btn.setFixedWidth(64)
        self.add_btn.clicked.connect(self.add_task_action)
        title_row.addWidget(self.add_btn)

        add_layout.addLayout(title_row)

        # Collapsible Details & Date row
        self.details_row = QHBoxLayout()
        self.details_row.setSpacing(8)

        self.quick_notes_input = QLineEdit()
        self.quick_notes_input.setPlaceholderText("Details / Notes (optional)")
        self.quick_notes_input.returnPressed.connect(self.add_task_action)
        self.details_row.addWidget(self.quick_notes_input)

        self.due_check = QCheckBox("Due:")
        self.details_row.addWidget(self.due_check)

        self.quick_date_picker = QDateEdit()
        self.quick_date_picker.setCalendarPopup(True)
        self.quick_date_picker.setDate(QDate.currentDate())
        self.quick_date_picker.setEnabled(False)
        self.details_row.addWidget(self.quick_date_picker)

        self.quick_time_picker = QTimeEdit()
        self.quick_time_picker.setTime(QTime(12, 0))
        self.quick_time_picker.setEnabled(False)
        self.details_row.addWidget(self.quick_time_picker)

        self.due_check.toggled.connect(self.quick_date_picker.setEnabled)
        self.due_check.toggled.connect(self.quick_time_picker.setEnabled)

        add_layout.addLayout(self.details_row)
        main_layout.addWidget(add_frame)

        # Scroll Area for Task Cards
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setContentsMargins(0, 4, 0, 4)
        self.tasks_layout.setSpacing(8)
        self.tasks_layout.addStretch()

        self.scroll.setWidget(self.tasks_container)
        main_layout.addWidget(self.scroll)

    def _toggle_quick_star(self) -> None:
        self.is_quick_starred = not self.is_quick_starred
        self.quick_star_btn.setText("★" if self.is_quick_starred else "☆")
        self.quick_star_btn.setProperty("starred", "true" if self.is_quick_starred else "false")
        self.quick_star_btn.style().unpolish(self.quick_star_btn)
        self.quick_star_btn.style().polish(self.quick_star_btn)

    def add_task_action(self) -> None:
        title = self.quick_title_input.text().strip()
        if not title:
            return

        notes = self.quick_notes_input.text().strip()
        due_date = None
        due_time = None
        if self.due_check.isChecked():
            due_date = self.quick_date_picker.date().toString("yyyy-MM-dd")
            due_time = self.quick_time_picker.time().toString("HH:mm")

        self.db.add_task(
            title=title,
            notes=notes,
            due_date=due_date,
            due_time=due_time,
            is_starred=self.is_quick_starred,
        )

        # Reset inputs
        self.quick_title_input.clear()
        self.quick_notes_input.clear()
        self.due_check.setChecked(False)
        self.is_quick_starred = False
        self.quick_star_btn.setText("☆")
        self.quick_star_btn.setProperty("starred", "false")
        self.quick_star_btn.style().unpolish(self.quick_star_btn)
        self.quick_star_btn.style().polish(self.quick_star_btn)

        self.refresh_tasks()
        self.tasks_changed.emit()

    def refresh_tasks(self) -> None:
        """Reload all active tasks from database and reconstruct task cards."""
        # Clear existing task widgets
        while self.tasks_layout.count():
            item = self.tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        active_tasks = self.db.get_active_tasks()

        if not active_tasks:
            empty_label = QLabel("All tasks completed! Enjoy your day 🎉")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setObjectName("mutedText")
            empty_label.setContentsMargins(0, 40, 0, 40)
            self.tasks_layout.addWidget(empty_label)
        else:
            for task in active_tasks:
                card = TaskCardWidget(task, self.db, self)
                card.task_completed.connect(self._on_task_completed)
                card.task_updated.connect(self._on_task_updated)
                card.task_deleted.connect(self._on_task_deleted)
                self.tasks_layout.addWidget(card)

        self.tasks_layout.addStretch()

    def _on_task_completed(self, task_id: int) -> None:
        self.refresh_tasks()
        self.tasks_changed.emit()

    def _on_task_updated(self) -> None:
        self.refresh_tasks()
        self.tasks_changed.emit()

    def _on_task_deleted(self, task_id: int) -> None:
        self.refresh_tasks()
        self.tasks_changed.emit()
