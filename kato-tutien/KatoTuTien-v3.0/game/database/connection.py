"""SQLite connection + safe transaction wrapper.

All repository operations can keep using Database.execute(); inside a
transaction it no longer commits each statement independently. This keeps
business operations atomic without leaking SQL into services.
"""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class Database:
    def __init__(self, path: str | Path = "kato_tutien.db"):
        self.path = str(path)
        self._lock = threading.RLock()
        self._transaction_depth = 0
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA busy_timeout = 5000")

    def execute(self, sql: str, params=()):
        with self._lock:
            cur = self.conn.execute(sql, params)
            if self._transaction_depth == 0:
                self.conn.commit()
            return cur

    def executemany(self, sql: str, seq):
        with self._lock:
            cur = self.conn.executemany(sql, seq)
            if self._transaction_depth == 0:
                self.conn.commit()
            return cur

    def fetchone(self, sql: str, params=()):
        with self._lock:
            return self.conn.execute(sql, params).fetchone()

    def fetchall(self, sql: str, params=()):
        with self._lock:
            return self.conn.execute(sql, params).fetchall()

    @contextmanager
    def transaction(self) -> Iterator["Database"]:
        """Run multiple repository operations as one atomic transaction."""
        with self._lock:
            outermost = self._transaction_depth == 0
            self._transaction_depth += 1
            if outermost:
                self.conn.execute("BEGIN")
            try:
                yield self
            except Exception:
                if outermost:
                    self.conn.rollback()
                raise
            else:
                if outermost:
                    self.conn.commit()
            finally:
                self._transaction_depth -= 1

    def close(self) -> None:
        with self._lock:
            self.conn.close()
