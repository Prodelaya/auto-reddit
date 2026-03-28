"""Settings del proyecto: carga y valida variables de entorno al arrancar. Fallo rápido si falta alguna."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    deepseek_api_key: str
    telegram_bot_token: str
    telegram_chat_id: str
    reddit_api_key: str
    max_daily_opportunities: int = 8
    review_window_days: int = 7
    daily_review_limit: int = 8
    max_daily_deliveries: int = 8
    db_path: str = "auto_reddit.db"
    deepseek_model: str = "deepseek-chat"

    model_config = {"env_file": ".env"}


settings = Settings()
