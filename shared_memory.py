#!/usr/bin/env python3
"""
Shared Memory for 2-Agent System
"""

from datetime import datetime
from typing import Any


class SharedMemory:
    """Simple shared knowledge base for both agents"""

    def __init__(self):
        self.data = {
            'file_analyses': {},
            'study_plans': {},
            'communications': []
        }

    def store(self, key: str, value: Any):
        self.data[key] = value

    def get(self, key: str) -> Any:
        return self.data.get(key, {})

    def log_comm(self, from_agent: str, to_agent: str, message: str):
        comm = {
            'time': datetime.now().strftime('%H:%M:%S'),
            'from': from_agent,
            'to': to_agent,
            'message': message
        }
        self.data['communications'].append(comm)
        print(f" {from_agent} → {to_agent}: {message}")


# Global shared memory instance
shared_memory = SharedMemory()