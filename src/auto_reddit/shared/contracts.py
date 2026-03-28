"""Contratos Pydantic compartidos entre módulos. Ningún módulo importa de otro; solo de aquí y de config/."""

from enum import Enum

from pydantic import BaseModel, computed_field


class ContextQuality(str, Enum):
    """Indicador de degradación del contexto de hilo extraído para un post.

    - ``full``: recuperado vía reddit34 (árbol de replies, timestamps, sort=new garantizado)
    - ``partial``: recuperado vía reddit3 (lista recursiva, sin garantía de orden estricto)
    - ``degraded``: recuperado vía reddapi (flat, top comments, sin comment_id ni timestamps)
    """

    full = "full"
    partial = "partial"
    degraded = "degraded"


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


class RedditComment(BaseModel):
    """Comentario normalizado de Reddit, independiente del proveedor fuente.

    Campos opcionales (`None`) cuando el proveedor no los expone (ver api-strategy.md §9):
    - ``comment_id``, ``created_utc``, ``permalink``, ``parent_id``, ``depth``: ausentes en reddapi.
    """

    comment_id: str | None = None
    author: str | None = None
    body: str  # normalizado desde text/content/body/comment según proveedor
    score: int | None = None
    created_utc: int | None = None
    permalink: str | None = None
    parent_id: str | None = None
    depth: int | None = None
    source_api: str


class ThreadContext(BaseModel):
    """Contexto bruto normalizado de un hilo para un post seleccionado.

    Salida del paso de extracción de contexto (Change 3). No contiene decisiones de negocio.
    """

    candidate: RedditCandidate
    comments: list[RedditComment]
    comment_count: int
    quality: ContextQuality
    source_api: str
