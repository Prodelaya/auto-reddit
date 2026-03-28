"""Orquestador del proceso diario: conecta todos los módulos y ejecuta el flujo completo."""

import datetime
import logging

from auto_reddit.config.settings import settings
from auto_reddit.delivery import deliver_daily
from auto_reddit.evaluation import evaluate_batch
from auto_reddit.persistence.store import CandidateStore
from auto_reddit.reddit.client import collect_candidates
from auto_reddit.reddit.comments import fetch_thread_contexts
from auto_reddit.shared.contracts import AcceptedOpportunity

logger = logging.getLogger(__name__)


def run() -> None:
    """Entry point del pipeline diario."""
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )

    # Guardia de fin de semana: solo ejecutar de lunes a viernes (weekday 0–4).
    # Esta lógica vive aquí (main.py), no en el cron externo.
    today = datetime.date.today()
    if today.weekday() >= 5:
        logger.info(
            "Ejecución programada en fin de semana (%s) — pipeline omitido sin efectos secundarios",
            today.strftime("%A %d/%m/%Y"),
        )
        return

    logger.info("Iniciando pipeline auto-reddit")

    # Change 2: inicializar store de memoria operativa
    store = CandidateStore(settings.db_path)
    store.init_db()

    # Change 1: recoger candidatos de r/Odoo (ventana configurada por review_window_days, sin recorte)
    candidates = collect_candidates(settings)
    total_collected = len(candidates)
    logger.info("Candidatos recogidos: %d", total_collected)

    # Change 2: excluir posts con decisión final (sent / rejected)
    decided_ids = store.get_decided_post_ids()
    eligible = [c for c in candidates if c.post_id not in decided_ids]
    excluded_count = total_collected - len(eligible)

    # Change 2: ordenar por recencia descendente y aplicar recorte downstream
    eligible.sort(key=lambda c: c.created_utc, reverse=True)
    review_set = eligible[: settings.daily_review_limit]

    logger.info(
        "Memoria: excluidos=%d, elegibles=%d, revisión=%d",
        excluded_count,
        len(eligible),
        len(review_set),
    )

    # Change 3: enriquecer con contexto bruto del hilo
    thread_contexts = fetch_thread_contexts(review_set, settings)
    logger.info(
        "Contextos de hilo extraídos: %d/%d posts enriquecidos",
        len(thread_contexts),
        len(review_set),
    )

    # Change 4: evaluación IA
    evaluation_results = evaluate_batch(thread_contexts, settings)
    accepted_count = 0
    rejected_count = 0
    for result in evaluation_results:
        if isinstance(result, AcceptedOpportunity):
            store.save_pending_delivery(result.post_id, result.model_dump_json())
            accepted_count += 1
        else:
            store.save_rejected(result.post_id)
            rejected_count += 1
    skipped_count = len(thread_contexts) - len(evaluation_results)
    logger.info(
        "Evaluación IA: aceptados=%d, rechazados=%d, saltados=%d",
        accepted_count,
        rejected_count,
        skipped_count,
    )

    # Change 5: entrega Telegram (retry-first, cap max_daily_opportunities)
    # reviewed_post_count = len(review_set) para el resumen de producto (product.md §10)
    report = deliver_daily(store, settings, reviewed_post_count=len(review_set))
    logger.info(
        "Entrega Telegram: seleccionadas=%d (reintentos=%d, nuevas=%d), "
        "enviadas=%d, fallidas=%d, resumen=%s, expiradas_saltadas=%d",
        report.total_selected,
        report.retries,
        report.new,
        report.sent_ok,
        report.sent_failed,
        report.summary_sent,
        report.expired_skipped,
    )

    logger.info("Pipeline completado")


if __name__ == "__main__":
    run()
