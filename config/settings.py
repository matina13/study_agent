import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration for DeepSeek via OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
DEFAULT_MODEL = "deepseek/deepseek-chat-v3-0324:free"

# DeepSeek-optimized settings
TEMPERATURE = 0.7  # Good balance for study planning
MAX_TOKENS = 1000  # Reasonable for free tier
REQUEST_TIMEOUT = 30  # seconds

# Study Planning Configuration
STUDY_SESSION_DURATION = 45  # minutes
BREAK_DURATION = 15  # minutes
DEFAULT_DAILY_HOURS = 4
MAX_DAILY_HOURS = 8

# Priority Weights
PRIORITY_WEIGHTS = {
    1: 0.2,  # Low priority
    2: 0.4,
    3: 0.6,
    4: 0.8,
    5: 1.0   # High priority
}

# Difficulty Multipliers
DIFFICULTY_FACTORS = {
    "beginner": 1.0,
    "intermediate": 1.3,
    "advanced": 1.6,
    "expert": 2.0
}

# Study Methods
STUDY_METHODS = [
    "active_reading",
    "practice_problems",
    "flashcards",
    "summarization",
    "teaching_others",
    "spaced_repetition",
    "mind_mapping",
    "focused_practice"
]

# DeepSeek-specific prompting settings
# DeepSeek responds well to clear, structured prompts
PROMPT_STYLE = "structured"
USE_EXAMPLES = True
CONTEXT_LENGTH = 4000  # Conservative estimate

# File Paths
DATA_DIR = "data"
LOGS_DIR = "logs"

# Create directories
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Validation
if not OPENROUTER_API_KEY:
    print("Warning: OPENROUTER_API_KEY not found in environment variables")
    print("Please add it to your .env file")