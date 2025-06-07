#!/usr/bin/env python3
"""
Base Agent Class
"""

import os
from dotenv import load_dotenv
import openai
from shared_memory import shared_memory


class BaseAgent:
    """Simple base class for both agents"""

    def __init__(self, name: str):
        load_dotenv()
        self.name = name
        self.memory = shared_memory

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found")

        self.client = openai.OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
        print(f"{name} ready")

    def call_ai(self, prompt: str, max_tokens: int = 800) -> str:
        try:
            response = self.client.chat.completions.create(
                model="deepseek/deepseek-chat-v3-0324:free",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    def send_message(self, to_agent: str, message: str):
        self.memory.log_comm(self.name, to_agent, message)