"""Multi-tab notes editor module for Mint Tasks (Windows 11 Notepad style).

Supports dynamic tabs, plain text editing across any Linux file format,
unsaved changes indicator (*), status bar (Ln/Col, words, chars), and path sanitization.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QShortcut, QTextCursor
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class NoteEditorDocument(QWidget):
    """Container widget for an individual note document tab."""

    document_modified = pyqtSignal(bool)
    cursor_position_changed = pyqtSignal(int, int, int, int)  # line, col, words, chars

    def __init__(
        self,
        file_path: Optional[str] = None,
        initial_title: str = "Untitled",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.file_path: Optional[str] = file_path
        self.title: str = initial_title
        self.is_modified: bool = False
        self.init_ui()

        if self.file_path:
            self.load_file(self.file_path)

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Editor
        self.editor = QPlainTextEdit()
        font = QFont("Monospace", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.editor.setFont(font)
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.editor.textChanged.connect(self._on_text_changed)
        self.editor.cursorPositionChanged.connect(self._on_cursor_changed)

        layout.addWidget(self.editor)

    def _on_text_changed(self) -> None:
        if not self.is_modified:
            self.is_modified = True
            self.document_modified.emit(True)
        self._update_stats()

    def _on_cursor_changed(self) -> None:
        self._update_stats()

    def _update_stats(self) -> None:
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        text = self.editor.toPlainText()
        chars = len(text)
        words = len(text.split()) if text.strip() else 0
        self.cursor_position_changed.emit(line, col, words, chars)

    def load_file(self, file_path: str) -> bool:
        """Load text content from a sanitized file path."""
        try:
            path = Path(file_path).resolve()
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            self.editor.blockSignals(True)
            self.editor.setPlainText(content)
            self.editor.blockSignals(False)
            self.file_path = str(path)
            self.title = path.name
            self.is_modified = False
            self.document_modified.emit(False)
            self._update_stats()
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error Opening File", f"Could not open file: {e}")
            return False

    def save_file(self, file_path: Optional[str] = None) -> bool:
        """Save text content to file securely."""
        target = file_path or self.file_path
        if not target:
            return False

        try:
            path = Path(target).resolve()
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
            self.file_path = str(path)
            self.title = path.name
            self.is_modified = False
            self.document_modified.emit(False)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error Saving File", f"Could not save file: {e}")
            return False


class NotesWorkspaceTab(QWidget):
    """
    Main Multi-Tab Notes workspace managing multiple open documents,
    shortcuts (Ctrl+N, Ctrl+W, Ctrl+S, Ctrl+O), and bottom status bar.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.untitled_counter = 1
        self.init_ui()
        self.setup_shortcuts()
        # Open first blank note
        self.add_new_note()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 4)
        layout.setSpacing(4)

        # Tab Bar Controls / Action Strip
        top_bar = QHBoxLayout()
        top_bar.setSpacing(6)

        new_btn = QPushButton("+ New Note")
        new_btn.setToolTip("New Note (Ctrl+N)")
        new_btn.clicked.connect(self.add_new_note)
        top_bar.addWidget(new_btn)

        open_btn = QPushButton("📂 Open...")
        open_btn.setToolTip("Open File (Ctrl+O)")
        open_btn.clicked.connect(self.open_file_dialog)
        top_bar.addWidget(open_btn)

        save_btn = QPushButton("💾 Save")
        save_btn.setToolTip("Save Current Note (Ctrl+S)")
        save_btn.clicked.connect(self.save_current_file)
        top_bar.addWidget(save_btn)

        save_as_btn = QPushButton("Save As...")
        save_as_btn.setToolTip("Save As (Ctrl+Shift+S)")
        save_as_btn.clicked.connect(self.save_current_file_as)
        top_bar.addWidget(save_as_btn)

        top_bar.addStretch()
        layout.addLayout(top_bar)

        # Tab Widget for note documents
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_switched)
        layout.addWidget(self.tab_widget)

        # Bottom Status Bar for Note Stats
        self.status_bar_layout = QHBoxLayout()
        self.status_bar_layout.setContentsMargins(4, 2, 4, 2)

        self.pos_label = QLabel("Ln 1, Col 1")
        self.stats_label = QLabel("0 words, 0 chars")
        self.encoding_label = QLabel("UTF-8")
        self.format_label = QLabel("Plain Text")

        for lbl in (self.pos_label, self.stats_label, self.encoding_label, self.format_label):
            lbl.setObjectName("mutedText")
            lbl.setStyleSheet("font-size: 11px;")

        self.status_bar_layout.addWidget(self.pos_label)
        self.status_bar_layout.addSpacing(16)
        self.status_bar_layout.addWidget(self.stats_label)
        self.status_bar_layout.addStretch()
        self.status_bar_layout.addWidget(self.encoding_label)
        self.status_bar_layout.addSpacing(16)
        self.status_bar_layout.addWidget(self.format_label)

        layout.addLayout(self.status_bar_layout)

    def setup_shortcuts(self) -> None:
        """Configure keyboard shortcuts for quick editor workflows."""
        QShortcut(QKeySequence("Ctrl+N"), self, self.add_new_note)
        QShortcut(QKeySequence("Ctrl+W"), self, self.close_current_tab)
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_current_file)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, self.save_current_file_as)
        QShortcut(QKeySequence("Ctrl+O"), self, self.open_file_dialog)

    def current_doc(self) -> Optional[NoteEditorDocument]:
        widget = self.tab_widget.currentWidget()
        if isinstance(widget, NoteEditorDocument):
            return widget
        return None

    def add_new_note(self, file_path: Optional[str] = None) -> NoteEditorDocument:
        """Create a new note editor tab."""
        title = Path(file_path).name if file_path else f"Untitled-{self.untitled_counter}"
        if not file_path:
            self.untitled_counter += 1

        doc = NoteEditorDocument(file_path=file_path, initial_title=title, parent=self)
        doc.document_modified.connect(lambda mod, d=doc: self._on_doc_modified(d, mod))
        doc.cursor_position_changed.connect(self._on_cursor_stats)

        index = self.tab_widget.addTab(doc, title)
        self.tab_widget.setCurrentIndex(index)
        doc.editor.setFocus()
        return doc

    def _on_doc_modified(self, doc: NoteEditorDocument, modified: bool) -> None:
        idx = self.tab_widget.indexOf(doc)
        if idx != -1:
            title = doc.title
            if modified:
                self.tab_widget.setTabText(idx, f"*{title}")
            else:
                self.tab_widget.setTabText(idx, title)

    def _on_cursor_stats(self, line: int, col: int, words: int, chars: int) -> None:
        self.pos_label.setText(f"Ln {line}, Col {col}")
        self.stats_label.setText(f"{words} words, {chars} chars")
        doc = self.current_doc()
        if doc and doc.file_path:
            ext = Path(doc.file_path).suffix or "Plain Text"
            self.format_label.setText(ext)
        else:
            self.format_label.setText("Plain Text")

    def _on_tab_switched(self, index: int) -> None:
        doc = self.current_doc()
        if doc:
            doc._update_stats()

    def open_file_dialog(self) -> None:
        """Show open file dialog supporting any Linux plain text format."""
        filters = (
            "All Files (*.*);;"
            "Text Files (*.txt);;"
            "Markdown (*.md);;"
            "Python Scripts (*.py);;"
            "Shell Scripts (*.sh);;"
            "JSON (*.json);;"
            "YAML (*.yaml *.yml);;"
            "CSV (*.csv);;"
            "Log Files (*.log)"
        )
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            str(Path.home()),
            filters,
        )
        if file_path:
            # Check if file is already open
            for i in range(self.tab_widget.count()):
                w = self.tab_widget.widget(i)
                if isinstance(w, NoteEditorDocument) and w.file_path == file_path:
                    self.tab_widget.setCurrentIndex(i)
                    return

            self.add_new_note(file_path=file_path)

    def save_current_file(self) -> bool:
        """Save the active document tab."""
        doc = self.current_doc()
        if not doc:
            return False

        if doc.file_path:
            success = doc.save_file()
            self._on_doc_modified(doc, False)
            return success
        else:
            return self.save_current_file_as()

    def save_current_file_as(self) -> bool:
        """Show save file dialog for the active document tab."""
        doc = self.current_doc()
        if not doc:
            return False

        filters = (
            "Text Files (*.txt);;"
            "Markdown (*.md);;"
            "Python Scripts (*.py);;"
            "Shell Scripts (*.sh);;"
            "JSON (*.json);;"
            "YAML (*.yaml *.yml);;"
            "CSV (*.csv);;"
            "Log Files (*.log);;"
            "All Files (*.*)"
        )
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File As",
            str(Path.home() / (doc.title.lstrip("*"))),
            filters,
        )
        if file_path:
            success = doc.save_file(file_path)
            self._on_doc_modified(doc, False)
            return success
        return False

    def close_current_tab(self) -> None:
        self.close_tab(self.tab_widget.currentIndex())

    def close_tab(self, index: int) -> None:
        """Close document tab, prompting if unsaved changes exist."""
        if index < 0 or index >= self.tab_widget.count():
            return

        widget = self.tab_widget.widget(index)
        if isinstance(widget, NoteEditorDocument) and widget.is_modified:
            title = widget.title.lstrip("*")
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                f"Do you want to save changes to '{title}' before closing?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Save:
                self.tab_widget.setCurrentIndex(index)
                if not self.save_current_file():
                    return  # Save cancelled or failed
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        self.tab_widget.removeTab(index)
        widget.deleteLater()

        # Keep at least one blank tab open if all closed
        if self.tab_widget.count() == 0:
            self.add_new_note()

    def check_all_saved_before_exit(self) -> bool:
        """Check all tabs before application exit."""
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, NoteEditorDocument) and widget.is_modified:
                title = widget.title.lstrip("*")
                self.tab_widget.setCurrentIndex(i)
                reply = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    f"'{title}' has unsaved changes.\nSave before exiting?",
                    QMessageBox.StandardButton.Save
                    | QMessageBox.StandardButton.Discard
                    | QMessageBox.StandardButton.Cancel,
                )
                if reply == QMessageBox.StandardButton.Save:
                    if not self.save_current_file():
                        return False
                elif reply == QMessageBox.StandardButton.Cancel:
                    return False
        return True
