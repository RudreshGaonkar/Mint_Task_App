"""Multi-tab Notes workspace — Windows 11 Notepad Style, modern UI.

Flat tab strip with modified-dot indicator, format-agnostic editing,
monospace editor, real-time stats status bar, and keyboard shortcuts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
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
    """Single note editor tab."""

    document_modified = pyqtSignal(bool)
    cursor_stats_changed = pyqtSignal(int, int, int, int)  # ln, col, words, chars

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

        self.editor = QPlainTextEdit()
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.editor.textChanged.connect(self._on_text_changed)
        self.editor.cursorPositionChanged.connect(self._update_stats)
        layout.addWidget(self.editor)

    def _on_text_changed(self) -> None:
        if not self.is_modified:
            self.is_modified = True
            self.document_modified.emit(True)
        self._update_stats()

    def _update_stats(self) -> None:
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        text = self.editor.toPlainText()
        chars = len(text)
        words = len(text.split()) if text.strip() else 0
        self.cursor_stats_changed.emit(line, col, words, chars)

    def load_file(self, file_path: str) -> bool:
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
            QMessageBox.critical(self, "Error Opening File", str(e))
            return False

    def save_file(self, file_path: Optional[str] = None) -> bool:
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
            QMessageBox.critical(self, "Error Saving File", str(e))
            return False


class NotesWorkspaceTab(QWidget):
    """Multi-tab notes editor workspace."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.untitled_counter = 1
        self.init_ui()
        self.setup_shortcuts()
        self.add_new_note()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Tab toolbar ──────────────────────────────────────────────────────
        toolbar = QFrame()
        toolbar.setObjectName("addTaskBar")
        toolbar.setFixedHeight(48)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 0, 10, 0)
        toolbar_layout.setSpacing(6)

        new_btn = QPushButton("+ New")
        new_btn.setFixedHeight(30)
        new_btn.setToolTip("New Tab (Ctrl+N)")
        new_btn.clicked.connect(self.add_new_note)
        toolbar_layout.addWidget(new_btn)

        open_btn = QPushButton("📂 Open")
        open_btn.setFixedHeight(30)
        open_btn.setToolTip("Open File (Ctrl+O)")
        open_btn.clicked.connect(self.open_file_dialog)
        toolbar_layout.addWidget(open_btn)

        save_btn = QPushButton("💾 Save")
        save_btn.setObjectName("primaryBtn")
        save_btn.setFixedHeight(30)
        save_btn.setToolTip("Save (Ctrl+S)")
        save_btn.clicked.connect(self.save_current_file)
        toolbar_layout.addWidget(save_btn)

        save_as_btn = QPushButton("Save As…")
        save_as_btn.setFixedHeight(30)
        save_as_btn.setToolTip("Save As (Ctrl+Shift+S)")
        save_as_btn.clicked.connect(self.save_current_file_as)
        toolbar_layout.addWidget(save_as_btn)

        toolbar_layout.addStretch()
        layout.addWidget(toolbar)

        # ── Notes Tab Widget ─────────────────────────────────────────────────
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("notesTabWidget")
        self.tab_widget.tabBar().setObjectName("notesTabBar")
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_switched)
        layout.addWidget(self.tab_widget, stretch=1)

        # ── Status Bar ───────────────────────────────────────────────────────
        status_bar = QFrame()
        status_bar.setObjectName("statusBar")
        status_bar.setFixedHeight(26)
        sb_layout = QHBoxLayout(status_bar)
        sb_layout.setContentsMargins(10, 0, 10, 0)
        sb_layout.setSpacing(16)

        self.pos_label = QLabel("Ln 1, Col 1")
        self.pos_label.setObjectName("statusLabel")
        sb_layout.addWidget(self.pos_label)

        self.stats_label = QLabel("0 words, 0 chars")
        self.stats_label.setObjectName("statusLabel")
        sb_layout.addWidget(self.stats_label)

        sb_layout.addStretch()

        self.format_label = QLabel("Plain Text")
        self.format_label.setObjectName("statusLabel")
        sb_layout.addWidget(self.format_label)

        self.encoding_label = QLabel("UTF-8")
        self.encoding_label.setObjectName("statusLabel")
        sb_layout.addWidget(self.encoding_label)

        layout.addWidget(status_bar)

    def setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+N"), self, self.add_new_note)
        QShortcut(QKeySequence("Ctrl+W"), self, self.close_current_tab)
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_current_file)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, self.save_current_file_as)
        QShortcut(QKeySequence("Ctrl+O"), self, self.open_file_dialog)

    def current_doc(self) -> Optional[NoteEditorDocument]:
        w = self.tab_widget.currentWidget()
        if isinstance(w, NoteEditorDocument):
            return w
        return None

    def add_new_note(self, file_path: Optional[str] = None) -> NoteEditorDocument:
        title = Path(file_path).name if file_path else f"Untitled-{self.untitled_counter}"
        if not file_path:
            self.untitled_counter += 1

        doc = NoteEditorDocument(file_path=file_path, initial_title=title, parent=self)
        doc.document_modified.connect(lambda mod, d=doc: self._on_doc_modified(d, mod))
        doc.cursor_stats_changed.connect(self._on_cursor_stats)

        idx = self.tab_widget.addTab(doc, title)
        self.tab_widget.setCurrentIndex(idx)
        doc.editor.setFocus()
        return doc

    def _on_doc_modified(self, doc: NoteEditorDocument, modified: bool) -> None:
        idx = self.tab_widget.indexOf(doc)
        if idx != -1:
            base = doc.title.lstrip("* ")
            # Pulsating dot indicator for unsaved
            self.tab_widget.setTabText(idx, f"● {base}" if modified else base)

    def _on_cursor_stats(self, line: int, col: int, words: int, chars: int) -> None:
        self.pos_label.setText(f"Ln {line}, Col {col}")
        self.stats_label.setText(f"{words} words  ·  {chars} chars")
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
        filters = (
            "All Files (*.*);;"
            "Text Files (*.txt);;"
            "Markdown (*.md);;"
            "Python (*.py);;"
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
            options=QFileDialog.Option.DontUseNativeDialog
        )
        if not file_path:
            return

        # Bring to front if already open
        for i in range(self.tab_widget.count()):
            w = self.tab_widget.widget(i)
            if isinstance(w, NoteEditorDocument) and w.file_path == file_path:
                self.tab_widget.setCurrentIndex(i)
                return

        self.add_new_note(file_path=file_path)

    def save_current_file(self) -> bool:
        doc = self.current_doc()
        if not doc:
            return False
        if doc.file_path:
            success = doc.save_file()
            if success:
                self._on_doc_modified(doc, False)
            return success
        return self.save_current_file_as()

    def save_current_file_as(self) -> bool:
        doc = self.current_doc()
        if not doc:
            return False
        filters = (
            "Text Files (*.txt);;"
            "Markdown (*.md);;"
            "Python (*.py);;"
            "Shell Scripts (*.sh);;"
            "JSON (*.json);;"
            "YAML (*.yaml *.yml);;"
            "CSV (*.csv);;"
            "Log Files (*.log);;"
            "All Files (*.*)"
        )
        base_name = doc.title.lstrip("●● ")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File As",
            str(Path.home() / base_name),
            filters,
            options=QFileDialog.Option.DontUseNativeDialog
        )
        if file_path:
            success = doc.save_file(file_path)
            if success:
                self._on_doc_modified(doc, False)
            return success
        return False

    def close_current_tab(self) -> None:
        self.close_tab(self.tab_widget.currentIndex())

    def close_tab(self, index: int) -> None:
        if index < 0 or index >= self.tab_widget.count():
            return
        widget = self.tab_widget.widget(index)
        if isinstance(widget, NoteEditorDocument) and widget.is_modified:
            title = widget.title.lstrip("●● ")
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                f"Save changes to '{title}' before closing?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Save:
                self.tab_widget.setCurrentIndex(index)
                if not self.save_current_file():
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        self.tab_widget.removeTab(index)
        widget.deleteLater()
        if self.tab_widget.count() == 0:
            self.add_new_note()

    def check_all_saved_before_exit(self) -> bool:
        for i in range(self.tab_widget.count()):
            w = self.tab_widget.widget(i)
            if isinstance(w, NoteEditorDocument) and w.is_modified:
                title = w.title.lstrip("●● ")
                self.tab_widget.setCurrentIndex(i)
                reply = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    f"'{title}' has unsaved changes. Save before exiting?",
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
