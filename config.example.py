"""Example configuration file. Copy this to config.py and update with your settings."""

# OpenAI Configuration
OPENAI_API_KEY = "your_openai_api_key_here"
OPENAI_MODEL = "gpt-5-nano-2025-08-07"  # or "gpt-4o", "gpt-4o-mini" for alternatives

# Database Configuration
DATABASE_PATH = "one_piece_stocks.db"

# Crawler Configuration
CRAWLER_DELAY = 1.0  # Delay between requests in seconds (be respectful)

# Processing Configuration
DEFAULT_START_CHAPTER = 1
DEFAULT_MAX_CHAPTERS = None  # None = process all

