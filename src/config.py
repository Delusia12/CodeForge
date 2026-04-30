import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "claude-sonnet-4-6-20250514")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "gpt-4o")
REPORT_DIR = Path(os.getenv("REPORT_DIR", BASE_DIR / "reports"))

CODE_SMELL_THRESHOLDS = {
    "max_function_lines": 50,
    "max_cyclomatic_complexity": 10,
    "max_nesting_depth": 4,
    "max_parameters": 5,
}
