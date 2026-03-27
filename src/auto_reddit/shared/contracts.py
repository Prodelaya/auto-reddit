"""Contratos Pydantic compartidos entre módulos. Ningún módulo importa de otro; solo de aquí y de config/."""

from enum import Enum

from pydantic import BaseModel, computed_field


class PostDecision(str, Enum):
    """Decisiones de negocio finales y estado operativo pre-envío para un post."""

    sent = "sent"
    rejected = "rejected"
    pending_delivery = "pending_delivery"


class PostRecord(BaseModel):
    """Registro persistido de un post con su estado de decisión.

    - `sent` / `rejected`: decisiones finales de negocio.
    - `pending_delivery`: estado operativo transitorio (IA aceptó, Telegram aún no confirma).
    """

    post_id: str
    status: PostDecision
    opportunity_data: str | None = None
    decided_at: int  # Unix timestamp


class RedditCandidate(BaseModel):
    post_id: str
    title: str
    selftext: str | None = None
    url: str  # always full URL
    permalink: str  # always full URL
    author: str | None = None
    subreddit: str
    created_utc: int
    num_comments: int | None = None
    source_api: str

    @computed_field
    @property
    def is_complete(self) -> bool:
        """True only when ALL minimum-contract fields are present and non-empty.

        Minimum contract (change 1): post_id, title, url, permalink, subreddit,
        created_utc (non-zero), source_api, selftext (not None), author (not None).
        Fields deliberately optional (num_comments) do NOT affect completeness.
        """
        return bool(
            self.post_id
            and self.title
            and self.url
            and self.permalink
            and self.subreddit
            and self.created_utc  # 0 means unknown → incomplete
            and self.source_api
            and self.selftext is not None
            and self.author is not None
        )
