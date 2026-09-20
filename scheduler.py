"""Background notification and scheduler daemon for Mint Tasks.

Checks SQLite database periodically (every 30 seconds) for due tasks,
triggers desktop notifications via `notify-send` / DBus, and plays non-intrusive sound alerts.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
import time
from datetime import datetime
from typing import Callable, List, Optional
from database import DatabaseManager


def trigger_desktop_notification(title: str, message: str) -> bool:
    """
    Trigger a desktop notification using system `notify-send` safely with shell=False.
    """
    if shutil.which("notify-send"):
        try:
            cmd = [
                "notify-send",
                "-a", "Mint Tasks",
                "-i", "utilities-tasks",
                "-u", "normal",
                title,
                message or "Task is due now!",
            ]
            subprocess.run(cmd, shell=False, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            pass
    return False


def play_sound_alert() -> None:
    """
    Play a non-intrusive desktop sound alert if audio players/files are available.
    """
    sound_files = [
        "/usr/share/sounds/freedesktop/stereo/message.oga",
        "/usr/share/sounds/freedesktop/stereo/complete.oga",
        "/usr/share/sounds/gnome/default/alerts/glass.ogg",
        "/usr/share/sounds/linuxmint/stereo/dialog-information.ogg",
    ]

    # Try canberra-gtk-play first
    if shutil.which("canberra-gtk-play"):
        try:
            subprocess.run(
                ["canberra-gtk-play", "-i", "message"],
                shell=False,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return
        except Exception:
            pass

    # Try paplay / pw-play / aplay with sound files
    player = shutil.which("paplay") or shutil.which("pw-play") or shutil.which("aplay")
    if player:
        for sf in sound_files:
            if os.path.exists(sf):
                try:
                    subprocess.run(
                        [player, sf],
                        shell=False,
                        check=False,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return
                except Exception:
                    pass


class NotificationScheduler(threading.Thread):
    """
    Background daemon thread that periodically checks for due tasks and triggers alerts.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        interval_seconds: int = 30,
        on_due_callback: Optional[Callable[[List[dict]], None]] = None,
    ) -> None:
        super().__init__(daemon=True, name="MintTasksScheduler")
        self.db = db_manager
        self.interval = interval_seconds
        self.on_due_callback = on_due_callback
        self._stop_event = threading.Event()

    def stop(self) -> None:
        """Signal the scheduler thread to stop."""
        self._stop_event.set()

    def run(self) -> None:
        """Main loop checking for due tasks every interval seconds."""
        # Initial brief pause to let application boot smoothly
        time.sleep(2.0)
        while not self._stop_event.is_set():
            try:
                self.check_and_notify()
            except Exception:
                pass

            # Sleep in small slices to allow rapid shutdown response
            for _ in range(self.interval * 2):
                if self._stop_event.is_set():
                    break
                time.sleep(0.5)

    def check_and_notify(self) -> List[dict]:
        """Query due tasks, trigger notifications and mark them notified."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        due_tasks = self.db.get_due_unnotified_tasks(now_str)

        if due_tasks:
            for task in due_tasks:
                task_id = task["id"]
                title = f"Task Due: {task['title']}"
                notes = task.get("notes", "")
                due_time = task.get("due_time", "")
                msg = f"Due at {due_time}\n{notes}".strip() if due_time else (notes or "Task is due now!")

                # Send desktop notification
                trigger_desktop_notification(title, msg)
                # Mark notified in DB so alert is not repeated
                self.db.mark_notified(task_id)

            # Play alert sound once for the triggered batch
            play_sound_alert()

            # Trigger optional UI callback
            if self.on_due_callback:
                try:
                    self.on_due_callback(due_tasks)
                except Exception:
                    pass

        return due_tasks
