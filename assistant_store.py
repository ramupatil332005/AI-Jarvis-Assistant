"""Local SQLite storage for recent Jarvis conversations."""

import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class HistoryEntry:
    command: str
    response: str
    url: str | None
    created_at: str


class AssistantStore:
    """Persist a small, private conversation history on this computer."""

    def __init__(self, database_path: Path | None = None):
        if database_path is None:
            database_path = Path.home() / ".jarvis_assistant" / "history.sqlite3"
        database_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(database_path, check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock, self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command TEXT NOT NULL,
                    response TEXT NOT NULL,
                    url TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )

    def add(self, command: str, response: str, url: str | None) -> None:
        created_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT INTO history (command, response, url, created_at) "
                "VALUES (?, ?, ?, ?)",
                (command, response, url, created_at),
            )

    def recent(self, limit: int = 8) -> list[HistoryEntry]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT command, response, url, created_at FROM history "
                "ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [HistoryEntry(*row) for row in rows]

    def close(self) -> None:
        with self._lock:
            self._connection.close()
