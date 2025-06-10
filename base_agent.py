import os
from dotenv import load_dotenv
import openai
from SQLiteState import *


class BaseAgent:
    def __init__(self, name: str):
        load_dotenv()
        self.name = name
        self.current_user_id = None
        self.current_session_id = None

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print(f" OPENROUTER_API_KEY not found for {name}")
            self.client = None
        else:
            self.client = openai.OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

    def set_user(self, user_id: str):
        """Set current user"""
        self.current_user_id = user_id
        self.current_session_id = state.get(f"current_session:{user_id}")

    def call_ai(self, prompt: str, max_tokens: int = 800) -> str:
        """AI call with user context"""
        if not self.client:
            return "AI client not available - check OPENROUTER_API_KEY"

        if self.current_user_id:
            user = state.get(f"user:{self.current_user_id}", {})
            context = f"""User Context:
Learning Style: {user.get('style', 'visual')}
Agent: {self.name}

User Request: {prompt}"""
        else:
            context = prompt

        try:
            response = self.client.chat.completions.create(
                model="deepseek/deepseek-chat-v3-0324:free",
                messages=[{"role": "user", "content": context}],
                max_tokens=max_tokens,
                temperature=0.7
            )

            result = response.choices[0].message.content

            # Log activity if in session
            if self.current_session_id:
                log_activity(self.current_session_id, f"{self.name}: AI call")

            return result

        except Exception as e:
            return f"Error: {str(e)}"

    def send_message(self, to_agent: str, message: str):
        """Send message to another agent"""
        if self.current_session_id:
            log_activity(self.current_session_id, f"Message to {to_agent}: {message}")
        print(f" {self.name} → {to_agent}: {message}")
