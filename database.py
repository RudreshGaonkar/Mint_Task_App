"""Database module for Mint Tasks.

Manages SQLite storage, XDG compliant paths, POSIX security permissions (0700/0600),
WAL mode, foreign keys, and CRUD operations.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_xdg_data_dir() -> Path:
    """Return XDG Data Directory for mint_tasks (~/.local/share/mint_tasks)."""
    base = os.environ.get("XDG_DATA_HOME")
    if base:
        data_dir = Path(base) / "mint_tasks"
    else:
        data_dir = Path.home() / ".local" / "share" / "mint_tasks"
    return data_dir


def get_xdg_config_dir() -> Path:
    """Return XDG Config Directory for mint_tasks (~/.config/mint_tasks)."""
    base = os.environ.get("XDG_CONFIG_HOME")
    if base:
        config_dir = Path(base) / "mint_tasks"
    else:
        config_dir = Path.home() / ".config" / "mint_tasks"
    return config_dir


def get_xdg_cache_dir() -> Path:
    """Return XDG Cache Directory for mint_tasks (~/.cache/mint_tasks)."""
    base = os.environ.get("XDG_CACHE_HOME")
    if base:
        cache_dir = Path(base) / "mint_tasks"
    else:
        cache_dir = Path.home() / ".cache" / "mint_tasks"
    return cache_dir


def get_default_db_path() -> Path:
    """Return default database file path."""
    return get_xdg_data_dir() / "tasks.db"


def ensure_secure_dir(directory: Path) -> None:
    """Create directory with 0700 (rwx------) permissions."""
    directory.mkdir(parents=True, exist_ok=True)
    os.chmod(directory, 0o700)


def ensure_secure_file(file_path: Path) -> None:
    """Ensure file exists with 0600 (rw-------) permissions."""
    if not file_path.exists():
        file_path.touch(mode=0o600, exist_ok=True)
    os.chmod(file_path, 0o600)


class DatabaseManager:
    """Handles all SQLite database interactions with secure permissions and WAL mode."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        if db_path is None:
            self.db_path = get_default_db_path()
        else:
            self.db_path = Path(db_path)
        self._ensure_storage_ready()
        self._init_schema()

    def _ensure_storage_ready(self) -> None:
        """Create parent directory and secure database file."""
        ensure_secure_dir(self.db_path.parent)
        ensure_secure_file(self.db_path)

    def get_connection(self) -> sqlite3.Connection:
        """Open a new connection with Row factory and Pragmas enabled."""
        self._ensure_storage_ready()
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode and foreign key constraints
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_schema(self) -> None:
        """Initialize SQLite tables and indexes."""
        with self.get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parent_id INTEGER NULL REFERENCES tasks(id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    notes TEXT DEFAULT '',
                    due_date TEXT NULL,
                    due_time TEXT NULL,
                    is_completed INTEGER DEFAULT 0,
                    completed_at TEXT NULL,
                    is_starred INTEGER DEFAULT 0,
                    position INTEGER DEFAULT 0,
                    notified INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_tasks_parent
                ON tasks(parent_id);
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_tasks_completed
                ON tasks(is_completed, completed_at);
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_tasks_due
                ON tasks(is_completed, notified, due_date, due_time);
                """
            )
            conn.commit()

        # Enforce file permission on db file and WAL auxiliary files if created
        for ext in ("", "-wal", "-shm"):
            aux_file = Path(f"{self.db_path}{ext}")
            if aux_file.exists():
                os.chmod(aux_file, 0o600)

    # -------------------------------------------------------------------------
    # CRUD Operations
    # -------------------------------------------------------------------------

    def add_task(
        self,
        title: str,
        notes: str = "",
        due_date: Optional[str] = None,
        due_time: Optional[str] = None,
        parent_id: Optional[int] = None,
        is_starred: bool = False,
        position: int = 0,
    ) -> int:
        """Create a new task or subtask and return its generated ID."""
        now_iso = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tasks (
                    parent_id, title, notes, due_date, due_time,
                    is_completed, completed_at, is_starred, position,
                    notified, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 0, NULL, ?, ?, 0, ?, ?);
                """,
                (
                    parent_id,
                    title.strip(),
                    notes.strip(),
                    due_date,
                    due_time,
                    1 if is_starred else 0,
                    position,
                    now_iso,
                    now_iso,
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single task record by ID."""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE id = ?;", (task_id,)
            ).fetchone()
            if row:
                return dict(row)
            return None

    def update_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        notes: Optional[str] = None,
        due_date: Optional[str] = None,
        due_time: Optional[str] = None,
        is_starred: Optional[bool] = None,
        position: Optional[int] = None,
    ) -> bool:
        """Update fields of an existing task."""
        fields: List[str] = []
        values: List[Any] = []

        if title is not None:
            fields.append("title = ?")
            values.append(title.strip())
        if notes is not None:
            fields.append("notes = ?")
            values.append(notes.strip())
        if due_date is not None:
            fields.append("due_date = ?")
            values.append(due_date if due_date != "" else None)
            # Reset notified status if due timestamp changes
            fields.append("notified = 0")
        if due_time is not None:
            fields.append("due_time = ?")
            values.append(due_time if due_time != "" else None)
            fields.append("notified = 0")
        if is_starred is not None:
            fields.append("is_starred = ?")
            values.append(1 if is_starred else 0)
        if position is not None:
            fields.append("position = ?")
            values.append(position)

        if not fields:
            return False

        fields.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(task_id)

        query = f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0

    def complete_task(self, task_id: int, completed: bool = True) -> bool:
        """Mark task (and its subtasks) completed or uncompleted."""
        now_iso = datetime.now().isoformat() if completed else None
        is_comp_val = 1 if completed else 0

        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Update parent task
            cursor.execute(
                """
                UPDATE tasks
                SET is_completed = ?, completed_at = ?, updated_at = ?
                WHERE id = ?;
                """,
                (is_comp_val, now_iso, datetime.now().isoformat(), task_id),
            )
            # If completing parent task, complete subtasks as well
            if completed:
                cursor.execute(
                    """
                    UPDATE tasks
                    SET is_completed = ?, completed_at = ?, updated_at = ?
                    WHERE parent_id = ?;
                    """,
                    (is_comp_val, now_iso, datetime.now().isoformat(), task_id),
                )
            conn.commit()
            return cursor.rowcount > 0

    def complete_subtask(self, subtask_id: int, completed: bool = True) -> bool:
        """Mark an individual subtask completed."""
        now_iso = datetime.now().isoformat() if completed else None
        is_comp_val = 1 if completed else 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE tasks
                SET is_completed = ?, completed_at = ?, updated_at = ?
                WHERE id = ? AND parent_id IS NOT NULL;
                """,
                (is_comp_val, now_iso, datetime.now().isoformat(), subtask_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def restore_task(self, task_id: int) -> bool:
        """Restore a completed task and its subtasks to active status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE tasks
                SET is_completed = 0, completed_at = NULL, updated_at = ?
                WHERE id = ?;
                """,
                (datetime.now().isoformat(), task_id),
            )
            # Also restore any subtasks of this task
            cursor.execute(
                """
                UPDATE tasks
                SET is_completed = 0, completed_at = NULL, updated_at = ?
                WHERE parent_id = ?;
                """,
                (datetime.now().isoformat(), task_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_task_permanently(self, task_id: int) -> bool:
        """Permanent hard purge: strictly removes the task record and child subtasks from SQLite."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Explicit delete of subtasks followed by parent (foreign key on delete cascade will also ensure this)
            cursor.execute("DELETE FROM tasks WHERE parent_id = ?;", (task_id,))
            cursor.execute("DELETE FROM tasks WHERE id = ?;", (task_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear_history(self) -> int:
        """Batch-purges all completed rows (hard delete)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE is_completed = 1;")
            conn.commit()
            return cursor.rowcount

    def factory_reset(self) -> None:
        """Wipe database files (tasks.db, tasks.db-wal, tasks.db-shm) and restore empty state."""
        # Delete files
        for ext in ("", "-wal", "-shm"):
            f = Path(f"{self.db_path}{ext}")
            if f.exists():
                try:
                    f.unlink()
                except OSError:
                    pass
        # Re-initialize schema
        self._ensure_storage_ready()
        self._init_schema()

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all active top-level tasks ordered by:
        1. is_starred DESC
        2. position ASC
        3. due_date IS NULL ASC, due_date ASC, due_time ASC
        4. created_at DESC
        Each task dict includes a 'subtasks' key with its active and completed subtasks.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(
                """
                SELECT * FROM tasks
                WHERE parent_id IS NULL AND is_completed = 0
                ORDER BY
                    is_starred DESC,
                    position ASC,
                    CASE WHEN due_date IS NULL OR due_date = '' THEN 1 ELSE 0 END ASC,
                    due_date ASC,
                    CASE WHEN due_time IS NULL OR due_time = '' THEN 1 ELSE 0 END ASC,
                    due_time ASC,
                    created_at DESC;
                """
            ).fetchall()

            tasks = [dict(r) for r in rows]
            for task in tasks:
                sub_rows = cursor.execute(
                    """
                    SELECT * FROM tasks
                    WHERE parent_id = ?
                    ORDER BY is_completed ASC, position ASC, created_at ASC;
                    """,
                    (task["id"],),
                ).fetchall()
                task["subtasks"] = [dict(sr) for sr in sub_rows]
            return tasks

    def get_subtasks(self, parent_id: int) -> List[Dict[str, Any]]:
        """Get all subtasks for a parent task."""
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM tasks
                WHERE parent_id = ?
                ORDER BY is_completed ASC, position ASC, created_at ASC;
                """,
                (parent_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_history_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all completed tasks grouped/sorted by completed_at DESC.
        Returns top-level completed tasks with their subtasks.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(
                """
                SELECT * FROM tasks
                WHERE is_completed = 1 AND parent_id IS NULL
                ORDER BY completed_at DESC, id DESC;
                """
            ).fetchall()

            tasks = [dict(r) for r in rows]
            for task in tasks:
                sub_rows = cursor.execute(
                    """
                    SELECT * FROM tasks
                    WHERE parent_id = ?
                    ORDER BY completed_at DESC, id DESC;
                    """,
                    (task["id"],),
                ).fetchall()
                task["subtasks"] = [dict(sr) for sr in sub_rows]
            return tasks

    def get_due_unnotified_tasks(self, current_dt_str: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query tasks where is_completed = 0, notified = 0, and due timestamp <= current_dt_str.
        current_dt_str should be formatted as 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD'.
        """
        if current_dt_str is None:
            current_dt_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        date_part = current_dt_str[:10]
        time_part = current_dt_str[11:16] if len(current_dt_str) >= 16 else "23:59"

        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM tasks
                WHERE is_completed = 0
                  AND notified = 0
                  AND due_date IS NOT NULL
                  AND due_date != ''
                  AND (
                      due_date < ?
                      OR (
                          due_date = ?
                          AND (
                              due_time IS NULL
                              OR due_time = ''
                              OR due_time <= ?
                          )
                      )
                  );
                """,
                (date_part, date_part, time_part),
            ).fetchall()
            return [dict(r) for r in rows]

    def mark_notified(self, task_id: int) -> None:
        """Mark task as notified so it is not repeatedly alerted."""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE tasks SET notified = 1 WHERE id = ?;", (task_id,)
            )
            conn.commit()
