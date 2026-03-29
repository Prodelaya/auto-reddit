"""Root conftest — runs before any test module is imported.

Sets dummy env vars so Settings() can be instantiated at collection time
without real credentials.  Tests that need real values override them via
their own fixtures or monkeypatch.
"""

import os

os.environ.setdefault("DEEPSEEK_API_KEY", "dummy-deepseek-key")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "dummy-telegram-token")
os.environ.setdefault("TELEGRAM_CHAT_ID", "dummy-telegram-chat-id")
os.environ.setdefault("REDDIT_API_KEY", "dummy-reddit-key")
