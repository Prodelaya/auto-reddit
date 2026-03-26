"""Contratos Pydantic compartidos entre módulos. Ningún módulo importa de otro; solo de aquí y de config/."""

# Aquí irán los modelos de contrato que fluyen entre módulos.
# Ejemplo (pendiente de implementar en el change correspondiente):
#
# class RedditPost(BaseModel):
#     post_id: str
#     title: str
#     body: str
#     url: str
#     comments: list[str]
#     created_at: datetime
#
# class EvaluationResult(BaseModel):
#     post_id: str
#     is_opportunity: bool
#     category: str | None
#     summary: str | None
#     suggested_reply: str | None
