import sqlite3
from pathlib import Path

# Database lives next to the project root (one level above this package)
DB_PATH = Path(__file__).resolve().parent.parent / "nexus_pos.db"


def get_db() -> sqlite3.Connection:
    """Return a new SQLite connection with Row factory and FK support."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
