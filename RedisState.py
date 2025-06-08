# RedisState.py
import redis
import json
import uuid
from datetime import datetime


class RedisState:
    def __init__(self):
        try:
            self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            self.r.ping()
            self.use_redis = True
            print("✅ Redis connected")
        except:
            self.r = {}  # Fallback to dict
            self.use_redis = False
            print("⚠️  Using memory fallback")

    def set(self, key, value, expire=None):
        """Set any value with optional expiration"""
        if self.use_redis:
            self.r.set(f"study:{key}", json.dumps(value), ex=expire)
        else:
            self.r[f"study:{key}"] = value  # Store directly as dict in fallback

    def get(self, key, default=None):
        """Get any value"""
        if self.use_redis:
            data = self.r.get(f"study:{key}")
            if data:
                try:
                    return json.loads(data)
                except (json.JSONDecodeError, TypeError):
                    return data
            return default
        else:
            # Fallback mode - data is already a dict, no JSON parsing needed
            return self.r.get(f"study:{key}", default)

    def push(self, key, value, max_items=100):
        """Add to list (FIFO)"""
        if self.use_redis:
            self.r.lpush(f"study:{key}", json.dumps(value))
            self.r.ltrim(f"study:{key}", 0, max_items - 1)
        else:
            if f"study:{key}" not in self.r:
                self.r[f"study:{key}"] = []
            self.r[f"study:{key}"].insert(0, value)
            self.r[f"study:{key}"] = self.r[f"study:{key}"][:max_items]

    def get_list(self, key, limit=20):
        """Get list items"""
        if self.use_redis:
            items = self.r.lrange(f"study:{key}", 0, limit - 1)
            result = []
            for item in items:
                try:
                    result.append(json.loads(item))
                except (json.JSONDecodeError, TypeError):
                    result.append(item)
            return result
        else:
            return self.r.get(f"study:{key}", [])[:limit]


# Global state instance
state = RedisState()


# Add this function to clear corrupted data
def clear_all_data():
    """Clear all data - use if you get JSON errors"""
    if state.use_redis:
        keys = state.r.keys("study:*")
        if keys:
            state.r.delete(*keys)
            print("🗑️ Cleared all Redis data")
    else:
        state.r.clear()
        print("🗑️ Cleared all memory data")


# Helper functions - just one-liners!
def create_user():
    user_id = str(uuid.uuid4())
    state.set(f"user:{user_id}", {"created": datetime.now().isoformat(), "style": "visual"})
    return user_id


def get_user(user_id):
    return state.get(f"user:{user_id}", {})


def start_session(user_id, subject):
    session_id = str(uuid.uuid4())
    session = {"id": session_id, "user": user_id, "subject": subject, "start": datetime.now().isoformat(),
               "activities": []}
    state.set(f"session:{session_id}", session)
    state.set(f"current_session:{user_id}", session_id, expire=86400)  # 24h expire
    return session_id


def log_activity(session_id, activity):
    session = state.get(f"session:{session_id}", {})
    if session:  # Check if session exists
        session["activities"] = session.get("activities", []) + [
            {"time": datetime.now().strftime("%H:%M"), "activity": activity}]
        state.set(f"session:{session_id}", session)


def end_session(session_id):
    session = state.get(f"session:{session_id}", {})
    if session:  # Check if session exists
        session["end"] = datetime.now().isoformat()
        state.set(f"session:{session_id}", session)
        if "user" in session:  # Check if user field exists
            state.push(f"sessions:{session['user']}", session)  # Add to user's session history


def save_content(user_id, filename, content_type, content):
    content_id = str(uuid.uuid4())
    data = {"id": content_id, "user": user_id, "filename": filename, "type": content_type, "content": content,
            "created": datetime.now().isoformat()}
    state.set(f"content:{content_id}", data)
    state.push(f"user_content:{user_id}", data)
    return content_id


def get_user_sessions(user_id, limit=10):
    return state.get_list(f"sessions:{user_id}", limit)


def get_user_content(user_id, limit=10):
    return state.get_list(f"user_content:{user_id}", limit)


def get_analytics(user_id):
    sessions = get_user_sessions(user_id, 50)
    total_hours = sum(1 for s in sessions if s.get("end"))  # Simplified
    subjects = list(set(s.get("subject", "Unknown") for s in sessions if s.get("subject")))  # Handle missing subjects
    return {"sessions": len(sessions), "hours": total_hours, "subjects": subjects}