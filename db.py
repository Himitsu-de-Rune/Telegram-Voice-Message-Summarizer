import sqlite3
from contextlib import closing

DB_NAME = "users.db"

def init_db():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                state TEXT,
                voice_text TEXT,
                mark INTEGER,
                count INTEGER DEFAULT 0,
                lang TEXT DEFAULT 'ru',
                progress INTEGER DEFAULT 0,
                start_time REAL,
                photos TEXT
            )
            """)

def get_user(chat_id: int) -> dict:
    with closing(sqlite3.connect(DB_NAME)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,)).fetchone()
        return dict(row) if row else None

def save_user(chat_id: int, **kwargs):
    user = get_user(chat_id)
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with conn:
            if user:
                fields = ", ".join([f"{k}=?" for k in kwargs.keys()])
                values = list(kwargs.values()) + [chat_id]
                conn.execute(f"UPDATE users SET {fields} WHERE chat_id=?", values)
            else:
                conn.execute("""
                    INSERT INTO users (chat_id, state, voice_text, mark, count, lang, progress, start_time, photos)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    chat_id,
                    kwargs.get("state"),
                    kwargs.get("voice_text"),
                    kwargs.get("mark"),
                    kwargs.get("count", 0),
                    kwargs.get("lang", "ru"),
                    kwargs.get("progress", 0),
                    kwargs.get("start_time"),
                    kwargs.get("photos", "photo1,photo2,photo3,photo4")
                ))