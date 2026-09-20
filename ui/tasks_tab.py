"""Tasks tab module — Modern Material Design 3 Task Cards.

Floating card layout with soft elevation (QGraphicsDropShadowEffect),
circular checkboxes, animated task completion, and collapsible subtasks
with connector lines.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import (
    QDate,
    QEasingCurve,
    QPropertyAnimation,
    QSize,
    Qt,
    QTime,
    pyqtSignal,
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGraphicsDropShadowEffect,
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
from theme import DarkPalette, LightPalette, load_config


def _make_shadow(theme: str = "dark") -> QGraphicsDropShadowEffect:
    """Create soft card elevation drop shadow."""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(16)
    shadow.setOffset(0, 4)
    if theme == "dark":
        shadow.setColor(QColor(0, 0, 0, 100))
    else:
        shadow.setColor(QColor(0, 0, 0, 33))
    return shadow


class SubtaskWidget(QFrame):
    """Individual subtask row within a task card."""

    subtask_toggled = pyqtSignal(int, bool)
    subtask_deleted = pyqtSignal(int)

    def __init__(self, subtask_data: Dict[str, Any], theme: str = "dark", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.subtask_data = subtask_data
        self.subtask_id = subtask_data["id"]
        self.theme = theme
        self.setObjectName("subtaskCard")
        self.init_ui()

    def init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(bool(self.subtask_data.get("is_completed", 0)))
        self.checkbox.toggled.connect(self._on_toggled)
        layout.addWidget(self.checkbox)

        self.title_label = QLabel(self.subtask_data.get("title", ""))
        self.title_label.setObjectName("taskTitle")
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._update_style()
        layout.addWidget(self.title_label)

        del_btn = QPushButton("✕")
        del_btn.setObjectName("iconBtn")
        del_btn.setFixedSize(22, 22)
        del_btn.setToolTip("Delete subtask")
        del_btn.clicked.connect(lambda: self.subtask_deleted.emit(self.subtask_id))
        layout.addWidget(del_btn)

    def _update_style(self) -> None:
        if self.checkbox.isChecked():
            self.title_label.setObjectName("taskTitleDone")
            font = self.title_label.font()
            font.setStrikeOut(True)
            self.title_label.setFont(font)
        else:
            self.title_label.setObjectName("taskTitle")
            font = self.title_label.font()
            font.setStrikeOut(False)
            self.title_label.setFont(font)
        self.title_label.style().unpolish(self.title_label)
        self.title_label.style().polish(self.title_label)

    def _on_toggled(self, checked: bool) -> None:
        self._update_style()
        self.subtask_toggled.emit(self.subtask_id, checked)


class TaskCardWidget(QFrame):
    """Modern floating task card with elevation shadow."""

    task_completed = pyqtSignal(int)
    task_updated = pyqtSignal()
    task_deleted = pyqtSignal(int)

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
        self.theme = theme
        self.setObjectName("taskCard")

        # Drop shadow (elevation)
        self.setGraphicsEffect(_make_shadow(theme))

        self.init_ui()

    def init_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(8)

        # ── Top row ──────────────────────────────────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(8)

        # Circular checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setToolTip("Mark completed")
        self.checkbox.toggled.connect(self._on_complete)
        top.addWidget(self.checkbox)

        # Star
        self.star_btn = QPushButton("★" if self.task_data.get("is_starred") else "☆")
        self.star_btn.setObjectName("starBtn")
        self.star_btn.setProperty("starred", "true" if self.task_data.get("is_starred") else "false")
        self.star_btn.setFixedSize(28, 28)
        self.star_btn.setToolTip("Star priority")
        self.star_btn.clicked.connect(self._toggle_star)
        top.addWidget(self.star_btn)

        # Title
        self.title_label = QLabel(self.task_data.get("title", ""))
        self.title_label.setObjectName("taskTitle")
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top.addWidget(self.title_label)

        # Due date badge
        self._add_due_badge(top)

        # Edit button
        edit_btn = QPushButton("✎")
        edit_btn.setObjectName("iconBtn")
        edit_btn.setFixedSize(28, 28)
        edit_btn.setToolTip("Edit")
        edit_btn.clicked.connect(self._open_edit_dialog)
        top.addWidget(edit_btn)

        # Delete button
        del_btn = QPushButton("🗑")
        del_btn.setObjectName("iconBtn")
        del_btn.setFixedSize(28, 28)
        del_btn.setToolTip("Delete permanently")
        del_btn.clicked.connect(self._on_delete)
        top.addWidget(del_btn)

        outer.addLayout(top)

        # ── Notes snippet ────────────────────────────────────────────────────
        notes = self.task_data.get("notes", "").strip()
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setObjectName("mutedLabel")
            notes_lbl.setWordWrap(True)
            notes_lbl.setContentsMargins(36, 0, 0, 0)
            outer.addWidget(notes_lbl)

        # ── Subtasks container ───────────────────────────────────────────────
        self.subtasks_layout = QVBoxLayout()
        self.subtasks_layout.setContentsMargins(24, 0, 0, 0)
        self.subtasks_layout.setSpacing(4)
        outer.addLayout(self.subtasks_layout)

        self._render_subtasks()

        # ── Inline subtask add bar ───────────────────────────────────────────
        sub_row = QHBoxLayout()
        sub_row.setContentsMargins(30, 0, 0, 0)
        sub_row.setSpacing(6)

        self.sub_input = QLineEdit()
        self.sub_input.setPlaceholderText("Add a subtask…")
        self.sub_input.returnPressed.connect(self._add_subtask)
        sub_row.addWidget(self.sub_input)

        add_sub_btn = QPushButton("+")
        add_sub_btn.setFixedSize(28, 28)
        add_sub_btn.clicked.connect(self._add_subtask)
        sub_row.addWidget(add_sub_btn)

        outer.addLayout(sub_row)

    def _add_due_badge(self, layout: QHBoxLayout) -> None:
        due_date = self.task_data.get("due_date")
        due_time = self.task_data.get("due_time") or ""
        if not due_date:
            return

        today = datetime.now().strftime("%Y-%m-%d")
        badge = QLabel()
        display = due_date if not due_time else f"{due_date} {due_time}"

        if due_date < today:
            badge.setObjectName("badgeOverdue")
            badge.setText(f"⚠ {display}")
        elif due_date == today:
            badge.setObjectName("badgeToday")
            badge.setText(f"Today {due_time}".strip())
        else:
            badge.setObjectName("badgeUpcoming")
            badge.setText(f"📅 {display}")

        layout.addWidget(badge)

    def _render_subtasks(self) -> None:
        while self.subtasks_layout.count():
            item = self.subtasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for sub in self.task_data.get("subtasks", []):
            sw = SubtaskWidget(sub, self.theme, self)
            sw.subtask_toggled.connect(self._on_subtask_toggled)
            sw.subtask_deleted.connect(self._on_subtask_deleted)
            self.subtasks_layout.addWidget(sw)

    def _on_subtask_toggled(self, sid: int, checked: bool) -> None:
        self.db.complete_subtask(sid, checked)

    def _on_subtask_deleted(self, sid: int) -> None:
        self.db.delete_task_permanently(sid)
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
        new_state = not bool(self.task_data.get("is_starred", 0))
        self.db.update_task(self.task_id, is_starred=new_state)
        self.task_updated.emit()

    def _on_complete(self, checked: bool) -> None:
        if not checked:
            return
        # Strike-through then animated fade-out
        font = self.title_label.font()
        font.setStrikeOut(True)
        self.title_label.setFont(font)
        self.title_label.setObjectName("taskTitleDone")

        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(320)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)

        def _after_fade():
            self.db.complete_task(self.task_id, True)
            self.task_completed.emit(self.task_id)

        anim.finished.connect(_after_fade)
        anim.start()

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
        dlg = TaskEditDialog(self.task_data, self.theme, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            title, notes, due_date, due_time = dlg.get_values()
            self.db.update_task(
                self.task_id,
                title=title,
                notes=notes,
                due_date=due_date,
                due_time=due_time,
            )
            self.task_updated.emit()


class TaskEditDialog(QDialog):
    """Modern edit dialog with flat inputs."""

    def __init__(
        self,
        task_data: Dict[str, Any],
        theme: str = "dark",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.task_data = task_data
        self.setWindowTitle("Edit Task")
        self.setMinimumWidth(420)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl = QLabel("Title")
        lbl.setObjectName("mutedLabel")
        layout.addWidget(lbl)

        self.title_edit = QLineEdit(self.task_data.get("title", ""))
        layout.addWidget(self.title_edit)

        lbl2 = QLabel("Details / Notes")
        lbl2.setObjectName("mutedLabel")
        layout.addWidget(lbl2)

        self.notes_edit = QTextEdit(self.task_data.get("notes", ""))
        self.notes_edit.setMaximumHeight(80)
        layout.addWidget(self.notes_edit)

        # Due date / time
        self.has_due_cb = QCheckBox("Set Due Date & Time")
        cd = self.task_data.get("due_date")
        ct = self.task_data.get("due_time")
        self.has_due_cb.setChecked(bool(cd))
        layout.addWidget(self.has_due_cb)

        pickers = QHBoxLayout()
        pickers.setSpacing(8)

        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(
            QDate.fromString(cd, "yyyy-MM-dd") if cd else QDate.currentDate()
        )
        self.date_picker.setEnabled(bool(cd))

        self.time_picker = QTimeEdit()
        self.time_picker.setTime(
            QTime.fromString(ct, "HH:mm") if ct else QTime(12, 0)
        )
        self.time_picker.setEnabled(bool(cd))

        self.has_due_cb.toggled.connect(self.date_picker.setEnabled)
        self.has_due_cb.toggled.connect(self.time_picker.setEnabled)

        pickers.addWidget(self.date_picker)
        pickers.addWidget(self.time_picker)
        layout.addLayout(pickers)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self) -> tuple:
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
    """Tasks view with modern floating cards and quick-add bar."""

    tasks_changed = pyqtSignal()

    def __init__(self, db: DatabaseManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.db = db
        self.theme = load_config().get("theme", "dark")
        self.init_ui()
        self.refresh_tasks()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Quick-Add Card ───────────────────────────────────────────────────
        add_card = QFrame()
        add_card.setObjectName("addTaskBar")
        add_card.setContentsMargins(0, 0, 0, 0)
        add_inner = QVBoxLayout(add_card)
        add_inner.setContentsMargins(14, 10, 14, 10)
        add_inner.setSpacing(8)

        # Title row
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        self.quick_star_btn = QPushButton("☆")
        self.quick_star_btn.setObjectName("starBtn")
        self.quick_star_btn.setFixedSize(28, 28)
        self.quick_star_btn.clicked.connect(self._toggle_quick_star)
        self.is_quick_starred = False
        title_row.addWidget(self.quick_star_btn)

        self.quick_title_input = QLineEdit()
        self.quick_title_input.setPlaceholderText("Add a task…")
        self.quick_title_input.returnPressed.connect(self.add_task_action)
        title_row.addWidget(self.quick_title_input)

        self.add_btn = QPushButton("Add")
        self.add_btn.setObjectName("primaryBtn")
        self.add_btn.setFixedWidth(70)
        self.add_btn.setFixedHeight(34)
        self.add_btn.clicked.connect(self.add_task_action)
        title_row.addWidget(self.add_btn)
        add_inner.addLayout(title_row)

        # Details / Date row
        detail_row = QHBoxLayout()
        detail_row.setSpacing(8)

        self.quick_notes_input = QLineEdit()
        self.quick_notes_input.setPlaceholderText("Details (optional)")
        detail_row.addWidget(self.quick_notes_input)

        self.due_check = QCheckBox("Due:")
        detail_row.addWidget(self.due_check)

        self.quick_date_picker = QDateEdit()
        self.quick_date_picker.setCalendarPopup(True)
        self.quick_date_picker.setDate(QDate.currentDate())
        self.quick_date_picker.setEnabled(False)
        self.quick_date_picker.setFixedWidth(105)
        detail_row.addWidget(self.quick_date_picker)

        self.quick_time_picker = QTimeEdit()
        self.quick_time_picker.setTime(QTime(12, 0))
        self.quick_time_picker.setEnabled(False)
        self.quick_time_picker.setFixedWidth(80)
        detail_row.addWidget(self.quick_time_picker)

        self.due_check.toggled.connect(self.quick_date_picker.setEnabled)
        self.due_check.toggled.connect(self.quick_time_picker.setEnabled)
        add_inner.addLayout(detail_row)

        layout.addWidget(add_card)
        layout.addSpacing(4)

        # ── Task Cards Scroll Area ───────────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.cards_widget = QWidget()
        self.cards_widget.setStyleSheet("background: transparent;")
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.setContentsMargins(0, 8, 0, 16)
        self.cards_layout.setSpacing(6)
        self.cards_layout.addStretch()

        self.scroll.setWidget(self.cards_widget)
        layout.addWidget(self.scroll, stretch=1)

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

        due_date = due_time = None
        if self.due_check.isChecked():
            due_date = self.quick_date_picker.date().toString("yyyy-MM-dd")
            due_time = self.quick_time_picker.time().toString("HH:mm")

        self.db.add_task(
            title=title,
            notes=self.quick_notes_input.text().strip(),
            due_date=due_date,
            due_time=due_time,
            is_starred=self.is_quick_starred,
        )

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
        # Update theme from config each refresh (handles toggles)
        self.theme = load_config().get("theme", "dark")

        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        active_tasks = self.db.get_active_tasks()

        if not active_tasks:
            empty = QLabel("No active tasks — enjoy your day! 🎉")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setObjectName("mutedLabel")
            empty.setContentsMargins(0, 48, 0, 48)
            self.cards_layout.addWidget(empty)
        else:
            for task in active_tasks:
                card = TaskCardWidget(task, self.db, self.theme, self)
                card.task_completed.connect(self._on_task_completed)
                card.task_updated.connect(self._on_task_updated)
                card.task_deleted.connect(self._on_task_deleted)
                self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def _on_task_completed(self, task_id: int) -> None:
        self.refresh_tasks()
        self.tasks_changed.emit()

    def _on_task_updated(self) -> None:
        self.refresh_tasks()
        self.tasks_changed.emit()

    def _on_task_deleted(self, task_id: int) -> None:
        self.refresh_tasks()
        self.tasks_changed.emit()
