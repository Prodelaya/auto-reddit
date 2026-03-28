"""Contratos Pydantic compartidos entre módulos. Ningún módulo importa de otro; solo de aquí y de config/."""

from enum import Enum
from typing import Annotated, Union

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


# ---------------------------------------------------------------------------
# Change 4: AI Opportunity Evaluation contracts
# ---------------------------------------------------------------------------


class OpportunityType(str, Enum):
    """Taxonomía cerrada de tipos de oportunidad en r/Odoo."""

    funcionalidad = "funcionalidad"
    desarrollo = "desarrollo"
    dudas_si_merece_la_pena = "dudas_si_merece_la_pena"
    comparativas = "comparativas"


class RejectionType(str, Enum):
    """Tipos de rechazo distintos para clasificación precisa del descarte."""

    resolved_or_closed = "resolved_or_closed"
    no_useful_contribution = "no_useful_contribution"
    excluded_topic = "excluded_topic"
    insufficient_evidence = "insufficient_evidence"


class AIRawResponse(BaseModel):
    """Respuesta estructurada devuelta por DeepSeek.

    Validada con Pydantic tras parsear el JSON. Los campos condicionales son
    opcionales porque solo aplican según ``accept``.

    - Campos de aceptación: solo presentes cuando ``accept=True``.
    - Campos de rechazo: solo presentes cuando ``accept=False``.
    - ``warning`` y ``human_review_bullets``: el modelo los puede incluir; solo se propagan al output final cuando ``accept=True`` (se descartan en ``RejectedPost``).
    """

    accept: bool

    # Campos de aceptación (presentes si accept=True)
    opportunity_type: OpportunityType | None = None
    opportunity_reason: str | None = None  # por qué la intervención aporta valor
    post_summary_es: str | None = None
    comment_summary_es: str | None = None
    suggested_response_es: str | None = None
    suggested_response_en: str | None = None
    post_language: str | None = (
        None  # único campo detectado por la IA (no determinístico)
    )

    # Campos de rechazo (presentes si accept=False)
    rejection_type: RejectionType | None = None

    # Contexto degradado: presente en ambos outcomes cuando quality=degraded
    warning: str | None = None
    human_review_bullets: list[str] | None = None


class AcceptedOpportunity(BaseModel):
    """Oportunidad aceptada por la IA.

    Combina campos determinísticos del pipeline (post_id, title, link) con los
    campos generados por la IA. ``model_dump_json()`` produce el JSON listo para
    persistir en ``opportunity_data``.
    """

    # Campos determinísticos del pipeline (no pedidos a la IA)
    post_id: str
    title: str
    link: str

    # Campos generados por la IA
    post_language: str
    opportunity_type: OpportunityType
    opportunity_reason: (
        str  # por qué la intervención aporta valor (distinto del resumen del post)
    )
    post_summary_es: str
    comment_summary_es: str | None = None  # None cuando no hay comentarios útiles
    suggested_response_es: str
    suggested_response_en: str

    # Contexto degradado — solo en oportunidades aceptadas con quality=degraded.
    # Los posts rechazados NO llevan warning ni bullets.
    warning: str | None = None
    human_review_bullets: list[str] | None = None


class RejectedPost(BaseModel):
    """Post rechazado por la IA con tipo de rechazo explícito."""

    post_id: str
    rejection_type: RejectionType


# Unión discriminada para el resultado de evaluación de un ThreadContext
EvaluationResult = Annotated[
    Union[AcceptedOpportunity, RejectedPost], "EvaluationResult"
]


# ---------------------------------------------------------------------------
# Change 5: Telegram Daily Delivery contracts
# ---------------------------------------------------------------------------


class DeliveryReport(BaseModel):
    """Informe de una ejecución de entrega Telegram diaria.

    - ``total_selected``: candidatos seleccionados por el selector (≤ cap).
    - ``retries``: registros reintentados (ya tenían intento previo fallido).
    - ``new``: registros nuevos (primer intento de entrega).
    - ``sent_ok``: mensajes individuales entregados con éxito a Telegram.
    - ``sent_failed``: mensajes individuales que fallaron en Telegram.
    - ``summary_sent``: True si el mensaje de resumen fue enviado con éxito.
    - ``expired_skipped``: registros excluidos por TTL expirado antes de selección.
    """

    total_selected: int
    retries: int
    new: int
    sent_ok: int
    sent_failed: int
    summary_sent: bool
    expired_skipped: int
