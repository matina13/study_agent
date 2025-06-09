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
        self.lock = threading.Lock()  # Thread safety
        self.init_database()
        print("✅ SQLite database initialized")

    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS key_value_store (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS list_store (
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (key, position)
                )
            ''')

            # Create indexes for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_list_key ON list_store(key)')
            conn.commit()

    def get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def set(self, key: str, value, expire=None):
        """Set any value (same interface as Redis)"""
        with self.lock:
            try:
                json_value = json.dumps(value)
                with self.get_connection() as conn:
                    conn.execute('''
                        INSERT OR REPLACE INTO key_value_store (key, value, updated_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                    ''', (f"study:{key}", json_value))
                    conn.commit()
            except Exception as e:
                print(f"Error setting key {key}: {e}")

    def get(self, key: str, default=None):
        """Get any value (same interface as Redis)"""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.execute(
                        'SELECT value FROM key_value_store WHERE key = ?',
                        (f"study:{key}",)
                    )
                    row = cursor.fetchone()

                    if row:
                        return json.loads(row['value'])
                    return default
            except Exception as e:
                print(f"Error getting key {key}: {e}")
                return default

    def push(self, key: str, value, max_items=100):
        """Add to list (same interface as Redis LPUSH)"""
        with self.lock:
            try:
                json_value = json.dumps(value)
                with self.get_connection() as conn:
                    # Get current max position
                    cursor = conn.execute(
                        'SELECT COALESCE(MAX(position), -1) as max_pos FROM list_store WHERE key = ?',
                        (f"study:{key}",)
                    )
                    max_pos = cursor.fetchone()['max_pos']

                    # Insert new item at position 0, shift others
                    conn.execute('''
                        UPDATE list_store 
                        SET position = position + 1 
                        WHERE key = ?
                    ''', (f"study:{key}",))

                    conn.execute('''
                        INSERT INTO list_store (key, value, position)
                        VALUES (?, ?, 0)
                    ''', (f"study:{key}", json_value))

                    # Remove items beyond max_items
                    conn.execute('''
                        DELETE FROM list_store 
                        WHERE key = ? AND position >= ?
                    ''', (f"study:{key}", max_items))

                    conn.commit()
            except Exception as e:
                print(f"Error pushing to list {key}: {e}")

    def get_list(self, key: str, limit=20):
        """Get list items (same interface as Redis LRANGE)"""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.execute('''
                        SELECT value FROM list_store 
                        WHERE key = ? 
                        ORDER BY position ASC 
                        LIMIT ?
                    ''', (f"study:{key}", limit))

                    result = []
                    for row in cursor:
                        try:
                            result.append(json.loads(row['value']))
                        except json.JSONDecodeError:
                            result.append(row['value'])  # Fallback for non-JSON data

                    return result
            except Exception as e:
                print(f"Error getting list {key}: {e}")
                return []

    def delete(self, key: str):
        """Delete a key"""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    conn.execute('DELETE FROM key_value_store WHERE key = ?', (f"study:{key}",))
                    conn.execute('DELETE FROM list_store WHERE key = ?', (f"study:{key}",))
                    conn.commit()
            except Exception as e:
                print(f"Error deleting key {key}: {e}")

    def clear_all_data(self):
        """Clear all data - equivalent to Redis FLUSHALL"""
        with self.lock:
            try:
                with self.get_connection() as conn:
                    conn.execute('DELETE FROM key_value_store')
                    conn.execute('DELETE FROM list_store')
                    conn.commit()
                print("🗑️ Cleared all SQLite data")
            except Exception as e:
                print(f"Error clearing data: {e}")

    def get_stats(self):
        """Get database statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('SELECT COUNT(*) as count FROM key_value_store')
                key_count = cursor.fetchone()['count']

                cursor = conn.execute('SELECT COUNT(DISTINCT key) as count FROM list_store')
                list_count = cursor.fetchone()['count']

                return {
                    'total_keys': key_count,
                    'total_lists': list_count,
                    'database_path': str(self.db_path.absolute())
                }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}

    def backup_database(self, backup_path: str = None):
        """Create a backup of the database"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"study_system_backup_{timestamp}.db"

        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            print(f"✅ Database backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"Error creating backup: {e}")
            return None


# Global state instance
state = SQLiteState()


# Helper functions - same interface as Redis version
def clear_all_data():
    """Clear all data"""
    state.clear_all_data()


def create_user():
    user_id = str(uuid.uuid4())
    state.set(f"user:{user_id}", {"created": datetime.now().isoformat(), "style": "visual"})
    return user_id


def get_user(user_id):
    return state.get(f"user:{user_id}", {})


def start_session(user_id, subject):
    session_id = str(uuid.uuid4())
    session = {
        "id": session_id,
        "user": user_id,
        "subject": subject,
        "start": datetime.now().isoformat(),
        "activities": []
    }
    state.set(f"session:{session_id}", session)
    state.set(f"current_session:{user_id}", session_id)  # No expiry needed
    return session_id


def log_activity(session_id, activity):
    session = state.get(f"session:{session_id}", {})
    if session:
        session["activities"] = session.get("activities", []) + [
            {"time": datetime.now().strftime("%H:%M"), "activity": activity}
        ]
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
    data = {
        "id": content_id,
        "user": user_id,
        "filename": filename,
        "type": content_type,
        "content": content,
        "created": datetime.now().isoformat()
    }
    state.set(f"content:{content_id}", data)
    state.push(f"user_content:{user_id}", data)
    return content_id


def get_user_sessions(user_id, limit=10):
    return state.get_list(f"sessions:{user_id}", limit)


def get_user_content(user_id, limit=10):
    return state.get_list(f"user_content:{user_id}", limit)


def get_analytics(user_id):
    sessions = get_user_sessions(user_id, 50)
    total_hours = sum(1 for s in sessions if s.get("end"))
    subjects = list(set(s.get("subject", "Unknown") for s in sessions if s.get("subject")))
    return {"sessions": len(sessions), "hours": total_hours, "subjects": subjects}


# Bonus: Database management functions
def get_database_stats():
    """Get database statistics"""
    return state.get_stats()


def backup_database(backup_path=None):
    """Create database backup"""
    return state.backup_database(backup_path)


def show_all_users():
    """Debug function to see all users"""
    try:
        with state.get_connection() as conn:
            cursor = conn.execute('''
                SELECT key, value FROM key_value_store 
                WHERE key LIKE 'study:user:%'
            ''')
            users = []
            for row in cursor:
                try:
                    user_data = json.loads(row['value'])
                    user_id = row['key'].replace('study:user:', '')
                    users.append({
                        'user_id': user_id,
                        'data': user_data
                    })
                except:
                    pass
            return users
    except Exception as e:
        print(f"Error getting users: {e}")
        return []