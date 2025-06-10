# SQLiteState.py
import sqlite3
import json
import uuid
import threading
from datetime import datetime
from pathlib import Path


class SQLiteState:
    def __init__(self):
        self.db_path = Path("study_system.db")
        self.lock = threading.Lock()
        self.init_db()
        print("SQLite database initialized")

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS data (
                key TEXT PRIMARY KEY, value TEXT)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS lists (
                key TEXT, value TEXT, pos INTEGER, 
                PRIMARY KEY (key, pos))''')
            conn.execute('''CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                learning_style TEXT DEFAULT 'visual',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def set(self, key, value, expire=None):
        with self.lock:
            try:
                with self.get_connection() as conn:
                    conn.execute('INSERT OR REPLACE INTO data VALUES (?, ?)',
                                 (f"study:{key}", json.dumps(value)))
            except Exception as e:
                print(f"Error setting {key}: {e}")

    def get(self, key, default=None):
        with self.lock:
            try:
                with self.get_connection() as conn:
                    row = conn.execute('SELECT value FROM data WHERE key = ?',
                                       (f"study:{key}",)).fetchone()
                    return json.loads(row['value']) if row else default
            except Exception as e:
                print(f"Error getting {key}: {e}")
                return default

    def push(self, key, value, max_items=100):
        with self.lock:
            try:
                with self.get_connection() as conn:
                    conn.execute('UPDATE lists SET pos = pos + 1 WHERE key = ?',
                                 (f"study:{key}",))
                    conn.execute('INSERT INTO lists VALUES (?, ?, 0)',
                                 (f"study:{key}", json.dumps(value)))
                    conn.execute('DELETE FROM lists WHERE key = ? AND pos >= ?',
                                 (f"study:{key}", max_items))
            except Exception as e:
                print(f"Error pushing to {key}: {e}")

    def get_list(self, key, limit=20):
        with self.lock:
            try:
                with self.get_connection() as conn:
                    rows = conn.execute('''SELECT value FROM lists 
                                        WHERE key = ? ORDER BY pos LIMIT ?''',
                                        (f"study:{key}", limit)).fetchall()
                    return [json.loads(row['value']) for row in rows]
            except Exception as e:
                print(f"Error getting list {key}: {e}")
                return []

    def store_user(self, user_id, username, learning_style='visual'):
        with self.lock:
            try:
                with self.get_connection() as conn:
                    conn.execute('''INSERT OR REPLACE INTO users 
                                    (user_id, username, learning_style)
                                    VALUES (?, ?, ?)''',
                                 (user_id, username, learning_style))
                return True
            except Exception as e:
                print(f"Error storing user: {e}")
                return False

    def find_by_username(self, username):
        with self.lock:
            try:
                with self.get_connection() as conn:
                    row = conn.execute('SELECT * FROM users WHERE username = ?',
                                       (username,)).fetchone()
                    return dict(row) if row else None
            except Exception as e:
                return None

    def get_stats(self):
        try:
            with self.get_connection() as conn:
                key_count = conn.execute('SELECT COUNT(*) FROM data').fetchone()[0]
                list_count = conn.execute('SELECT COUNT(DISTINCT key) FROM lists').fetchone()[0]
                user_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
                return {
                    'total_keys': key_count,
                    'total_lists': list_count,
                    'total_users': user_count,
                    'database_path': str(self.db_path.absolute())
                }
        except:
            return {}


# Global state
state = SQLiteState()


def get_user(user_id):
    return state.get(f"user:{user_id}", {})


def start_session(user_id, subject):
    session_id = str(uuid.uuid4())
    session = {"id": session_id, "user": user_id, "subject": subject,
               "start": datetime.now().isoformat(), "activities": []}
    state.set(f"session:{session_id}", session)
    state.set(f"current_session:{user_id}", session_id)
    return session_id


def log_activity(session_id, activity):
    session = state.get(f"session:{session_id}", {})
    if session:
        session["activities"] = session.get("activities", []) + [
            {"time": datetime.now().strftime("%H:%M"), "activity": activity}]
        state.set(f"session:{session_id}", session)


def end_session(session_id):
    session = state.get(f"session:{session_id}", {})
    if session:
        session["end"] = datetime.now().isoformat()
        state.set(f"session:{session_id}", session)
        if "user" in session:
            state.push(f"sessions:{session['user']}", session)


def save_content(user_id, filename, content_type, content):
    content_id = str(uuid.uuid4())
    data = {"id": content_id, "user": user_id, "filename": filename,
            "type": content_type, "content": content, "created": datetime.now().isoformat()}
    state.set(f"content:{content_id}", data)
    state.push(f"user_content:{user_id}", data)
    return content_id


def get_user_sessions(user_id, limit=10):
    return state.get_list(f"sessions:{user_id}", limit)


def get_user_content(user_id, limit=10):
    return state.get_list(f"user_content:{user_id}", limit)


def get_analytics(user_id):
    sessions = get_user_sessions(user_id, 50)
    subjects = list(set(s.get("subject", "Unknown") for s in sessions if s.get("subject")))
    return {"sessions": len(sessions), "subjects": subjects}
