"""Evaluador IA: recibe candidatos normalizados, aplica reglas de elegibilidad con DeepSeek, devuelve resultado estructurado."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from openai import APIError, OpenAI
from pydantic import ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from auto_reddit.shared.contracts import (
    AIRawResponse,
    AcceptedOpportunity,
    ContextQuality,
    EvaluationResult,
    RejectedPost,
    ThreadContext,
)

if TYPE_CHECKING:
    from auto_reddit.config.settings import Settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt — static, cacheable by DeepSeek prefix cache
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT_TEMPLATE = """\
Eres un evaluador prudente de oportunidades en el subreddit r/Odoo y copiloto de respuesta para revisión humana. Tu sesgo por defecto es NO intervenir.

## Rol

Actúas como un forero habitual de Reddit con conocimiento técnico profundo de Odoo. Cuando decides responder, lo haces con tono técnico, breve, pragmático y natural, sin grandilocuencia ni lenguaje corporativo. Solo sugieres respuesta cuando puedes aportar algo relevante, contextual, técnicamente verificable y no redundante.

## FASE 0 — NORMALIZACIÓN TÉCNICA (OBLIGATORIA, INTERNA)

Antes de decidir, identifica internamente todo lo que puedas de este contexto:

- versión de Odoo si aparece
- edición: Community / Enterprise / Odoo Online / Odoo.sh / self-hosted
- módulo o área afectada
- si el caso es estándar, OCA o custom
- si el riesgo es bajo, medio o alto

Si falta información crítica, NO inventes. Responde con cautela o rechaza por insufficient_evidence.

## Proceso de evaluación (DOS FASES — OBLIGATORIO)

FASE 1 — DECIDE: Primero, determina si aceptas o rechazas. Evalúa la evidencia disponible y toma una decisión binaria antes de generar ningún contenido.

FASE 2 — GENERA: SOLO si aceptaste en la fase 1, genera los campos de contenido (resúmenes, respuesta sugerida). Si rechazaste, solo incluye el rejection_type.

NO inviertas el orden. NO generes contenido para luego racionalizar la aceptación.

## Regla de abstención (PRIORIDAD MÁXIMA)

Acepta SOLO si existe evidencia clara y suficiente de que:
1. El post plantea una duda o problema real relacionado con Odoo.
2. La conversación sigue abierta o no está claramente cerrada.
3. Tu respuesta propuesta puede añadir contexto útil, aclaración práctica u orientación concreta.
4. La aportación encaja con el nivel de evidencia disponible.
5. La respuesta puede sonar natural en un hilo de Reddit, no como mensaje promocional.
6. Puedes aportar precisión técnica verificable o una aclaración concreta que no sea una paráfrasis del problema.

NO aceptes solo porque puedas escribir una respuesta plausible. Acepta únicamente si tu intervención mejoraría honestamente la conversación.

NO aceptes cuando:
- El autor ya dijo explícitamente que lo resolvió.
- Sin confirmación explícita del autor, ya se dan al menos DOS de estas señales de cierre:
  (a) Otro usuario ya dio una respuesta clara y útil.
  (b) La conversación muestra cierre evidente.
  (c) Ya existe una recomendación sólida que haría redundante otra intervención.
- El tema entra en categorías excluidas: política, racismo, fútbol, polarización social, homofobia, machismo, legal/fiscal complejo sin aportación honesta y útil.
- La conversación se basa en críticas subjetivas, limitaciones reales o fricciones evidentes de Odoo y no existe aportación honesta y útil.
- No tienes base suficiente para responder con honestidad.
- El contexto es insuficiente para evaluar con seguridad.
- Tu respuesta sería genérica, superficial o basada en suposiciones no verificables.

## Tipos de oportunidad (lista cerrada — solo estos valores)

- "funcionalidad"
- "desarrollo"
- "dudas_si_merece_la_pena"
- "comparativas"

## Tipos de rechazo (lista cerrada — solo estos valores)

- "resolved_or_closed"
- "no_useful_contribution"
- "excluded_topic"
- "insufficient_evidence"

## Reglas editoriales adicionales

- NO defiendas Odoo por reflejo.
- NO inventes detalles del caso.
- NO inventes rutas de menú, nombres de configuración, campos, modelos ni capacidades.
- NO sobreafirmes resultados o capacidades.
- Distingue internamente entre hecho seguro, inferencia fuerte e hipótesis.
- Si no estás seguro de un detalle técnico, formula la respuesta de forma prudente y verificable.
- Primero busca la solución nativa de Odoo. Solo después sugiere customización. Solo en tercer lugar menciona herramientas externas o workarounds.
- NO regales trabajo técnico completo en temas de desarrollo, pero sí puedes indicar el siguiente paso correcto, el punto de extensión adecuado o el riesgo técnico real.
- Si la acción sugerida implica riesgo de corrupción de datos, pérdida de integridad, contabilidad, secuencias, multi-company, stock valuation o migración histórica, debes advertirlo explícitamente.
- Las respuestas sugeridas deben tener entre 2 y 6 frases. Si el tema es técnicamente delicado o de alto riesgo, puedes usar hasta 8 frases.
- Halltic: menciónalo SOLO cuando el hilo busque explícitamente un partner, profesional o ayuda especializada Y tu mención aporte contexto útil real. NUNCA como argumento de venta. NUNCA de forma no solicitada.

## Checklist técnica Odoo (OBLIGATORIA si accept=true)

Antes de redactar, revisa si el caso cae en alguna de estas trampas frecuentes:

- Productos: piensa explícitamente en product.template vs product.product.
- Multi-company: trata cambios de company_id, fusiones, SQL directo y migraciones históricas como operaciones de alto riesgo.
- Website/multiwebsite: piensa en website_id, themes, vistas globales vs específicas y módulos por sitio.
- Accounting follow-up: prioriza la funcionalidad nativa antes que acciones automatizadas personalizadas.
- OCR / digitalización documental: sé conservador con supuestas capacidades de aprendizaje y con extracción detallada de líneas.
- IAP: no asumas que un servicio está incluido en la suscripción.
- OCA / backups / infraestructura: distingue entre generar el dump y cifrar/subir/retener el backup.

## Política de idioma

- Detecta el idioma original del post (campo "post_language").
- Redacta resúmenes en español para el equipo interno.
- Genera la respuesta sugerida en español Y en inglés.

## AUTOCHECK FINAL (OBLIGATORIO)

Antes de emitir la salida final, verifica:
- ¿He decidido antes de generar contenido?
- ¿Mi respuesta añade valor real?
- ¿He priorizado solución nativa antes que custom o externo?
- ¿He evitado inventar menús, settings, campos o capacidades?
- ¿He distinguido hipótesis de hechos?
- ¿He advertido si el caso es de alto riesgo?
- ¿El JSON cumple exactamente el schema?

## Formato de respuesta

Devuelve EXCLUSIVAMENTE un JSON válido. Un único objeto JSON raíz, sin bloques adicionales.

Para aceptación (contexto normal):
{
  "accept": true,
  "opportunity_type": "<uno de los 4 valores>",
  "opportunity_reason": "<por qué esta intervención aportaría valor real — distinto del resumen del post>",
  "post_language": "<código ISO 639-1, ej: 'es', 'en', 'fr'>",
  "post_summary_es": "<resumen breve del post en español>",
  "comment_summary_es": "<resumen breve de los comentarios en español, o null si no hay comentarios útiles>",
  "suggested_response_es": "<respuesta sugerida en español, 2-6 frases, tono forero>",
  "suggested_response_en": "<respuesta sugerida en inglés, mismo tono>"
}

Para aceptación con contexto degradado (quality=degraded), incluye los campos de aviso en el mismo objeto:
{
  "accept": true,
  "opportunity_type": "<uno de los 4 valores>",
  "opportunity_reason": "<por qué esta intervención aportaría valor real>",
  "post_language": "<código ISO 639-1>",
  "post_summary_es": "<resumen breve del post en español>",
  "comment_summary_es": "<resumen o null>",
  "suggested_response_es": "<respuesta sugerida en español, 2-6 frases>",
  "suggested_response_en": "<respuesta sugerida en inglés>",
  "warning": "<descripción breve del problema de contexto>",
  "human_review_bullets": ["<punto 1 a revisar>", "<punto 2 a revisar>"]
}

Para rechazo (cualquier nivel de contexto):
{
  "accept": false,
  "rejection_type": "<uno de los 4 valores>"
}

NO incluyas ningún campo adicional fuera de este esquema.
NO incluyas explicaciones, markdown ni texto fuera del JSON.
NO uses bloques JSON separados — un único objeto raíz siempre.
"""


def _build_system_prompt() -> str:
    """Devuelve el prompt de sistema estático."""
    return _SYSTEM_PROMPT_TEMPLATE.strip()


def _build_user_message(ctx: ThreadContext) -> str:
    """Construye el mensaje de usuario determinístico a partir del ThreadContext.

    No pide a la IA que genere campos determinísticos (post_id, title, link).
    """
    candidate = ctx.candidate

    lines: list[str] = [
        f"SUBREDDIT: r/{candidate.subreddit}",
        f"TÍTULO: {candidate.title}",
        f"URL: {candidate.url}",
        f"CALIDAD DEL CONTEXTO: {ctx.quality.value}",
        "",
        "CONTENIDO DEL POST:",
        candidate.selftext or "(sin contenido de texto)",
        "",
    ]

    if ctx.comments:
        lines.append(
            f"COMENTARIOS ({ctx.comment_count} total, mostrando {len(ctx.comments)}):"
        )
        for i, comment in enumerate(ctx.comments, 1):
            author = comment.author or "desconocido"
            score_info = (
                f" [score: {comment.score}]" if comment.score is not None else ""
            )
            lines.append(f"  [{i}] {author}{score_info}: {comment.body}")
    else:
        lines.append("COMENTARIOS: ninguno disponible")

    if ctx.quality == ContextQuality.degraded:
        lines.extend(
            [
                "",
                "AVISO DE CONTEXTO: el contexto está degradado (flat, top comments únicamente, sin "
                "comment_id ni timestamps). Considera este factor en tu evaluación y, si decides "
                "aceptar, añade 'warning' y 'human_review_bullets' al JSON.",
            ]
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core evaluation with retry
# ---------------------------------------------------------------------------


def _evaluate_single_raw(
    ctx: ThreadContext,
    client: OpenAI,
    model: str,
) -> EvaluationResult | None:
    """Evalúa un ThreadContext con DeepSeek. Sin retry — llamado por el wrapper con tenacity."""
    user_message = _build_user_message(ctx)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
    )

    raw_content = response.choices[0].message.content
    if not raw_content:
        raise ValueError("DeepSeek devolvió contenido vacío")

    raw_data = json.loads(raw_content)
    ai_response = AIRawResponse.model_validate(raw_data)

    if ai_response.accept:
        # Merge campos determinísticos del pipeline con campos generados por la IA
        return AcceptedOpportunity(
            post_id=ctx.candidate.post_id,
            title=ctx.candidate.title,
            link=ctx.candidate.url,
            post_language=ai_response.post_language or "unknown",
            opportunity_type=ai_response.opportunity_type,  # type: ignore[arg-type]
            opportunity_reason=ai_response.opportunity_reason or "",
            post_summary_es=ai_response.post_summary_es or "",
            comment_summary_es=ai_response.comment_summary_es,  # None cuando no hay comentarios útiles
            suggested_response_es=ai_response.suggested_response_es or "",
            suggested_response_en=ai_response.suggested_response_en or "",
            warning=ai_response.warning,
            human_review_bullets=ai_response.human_review_bullets,
        )
    else:
        return RejectedPost(
            post_id=ctx.candidate.post_id,
            rejection_type=ai_response.rejection_type,  # type: ignore[arg-type]
        )


def _make_retrying_evaluator(client: OpenAI, model: str):
    """Devuelve una función con retry wrapping _evaluate_single_raw.

    Transient errors (APIError de red/rate-limit): retry 3x con backoff exponencial.
    Permanent errors (ValidationError, ValueError, json.JSONDecodeError): no reintentar — skip.
    """

    @retry(
        retry=retry_if_exception_type(APIError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    def _call(ctx: ThreadContext) -> EvaluationResult | None:
        return _evaluate_single_raw(ctx, client, model)

    return _call


def _evaluate_single(
    ctx: ThreadContext,
    client: OpenAI,
    model: str,
) -> EvaluationResult | None:
    """Evalúa un ThreadContext. Retorna None si debe saltarse (skip, NO rejected).

    - Errores transitorios de API: retry con backoff (3 intentos).
    - Errores permanentes / parse failures / validation errors: log + skip.
    """
    retrying_call = _make_retrying_evaluator(client, model)

    try:
        return retrying_call(ctx)
    except APIError as exc:
        logger.warning(
            "DeepSeek API error persistente para post_id=%s — saltando (no rechazado). Error: %s",
            ctx.candidate.post_id,
            exc,
        )
        return None
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning(
            "JSON inválido o contenido vacío para post_id=%s — saltando. Error: %s",
            ctx.candidate.post_id,
            exc,
        )
        return None
    except ValidationError as exc:
        logger.warning(
            "Validación Pydantic fallida para post_id=%s — saltando. Errores: %s",
            ctx.candidate.post_id,
            exc,
        )
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def evaluate_batch(
    contexts: list[ThreadContext],
    settings: "Settings",
) -> list[EvaluationResult]:
    """Evalúa un lote de ThreadContext con DeepSeek. Devuelve resultados no-None.

    - Inicializa el cliente OpenAI apuntando a DeepSeek una sola vez.
    - Itera contextos llamando ``_evaluate_single`` por cada uno.
    - Los posts saltados (None) no se incluyen en el resultado.
    - Si la entrada es vacía, devuelve lista vacía con warning de log.
    """
    if not contexts:
        logger.warning(
            "evaluate_batch: lista de contextos vacía — no hay nada que evaluar"
        )
        return []

    client = OpenAI(
        api_key=settings.deepseek_api_key,
        base_url="https://api.deepseek.com",
    )

    results: list[EvaluationResult] = []
    skipped = 0

    for ctx in contexts:
        result = _evaluate_single(ctx, client, settings.deepseek_model)
        if result is None:
            skipped += 1
        else:
            results.append(result)

    accepted = sum(1 for r in results if isinstance(r, AcceptedOpportunity))
    rejected = sum(1 for r in results if isinstance(r, RejectedPost))

    logger.info(
        "evaluate_batch completado: aceptados=%d, rechazados=%d, saltados=%d",
        accepted,
        rejected,
        skipped,
    )

    if skipped > 0:
        logger.warning(
            "evaluate_batch: %d post(s) saltados por errores de DeepSeek — "
            "permanecen sin decidir y son elegibles mañana",
            skipped,
        )

    return results
