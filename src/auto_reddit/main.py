"""Orquestador del proceso diario: conecta todos los módulos y ejecuta el flujo completo."""

import logging

from auto_reddit.config.settings import settings
from auto_reddit.persistence.store import CandidateStore
from auto_reddit.reddit.client import collect_candidates
from auto_reddit.reddit.comments import fetch_thread_contexts

logger = logging.getLogger(__name__)


def run() -> None:
    """Entry point del pipeline diario."""
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )

    logger.info("Iniciando pipeline auto-reddit")

    # Change 2: inicializar store de memoria operativa
    store = CandidateStore(settings.db_path)
    store.init_db()

    # Change 1: recoger candidatos de r/Odoo (ventana 7 días, sin recorte)
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

    # Change 4 (pendiente): evaluación IA
    # for candidate in review_set:
    #     result = evaluate_candidate(candidate, settings)
    #     if result.is_opportunity:
    #         store.save_pending_delivery(candidate.post_id, result.model_dump_json())
    #     else:
    #         store.save_rejected(candidate.post_id)

    # Change 5 (pendiente): entrega Telegram
    # for record in store.get_pending_deliveries():
    #     success = deliver(record, settings)
    #     if success:
    #         store.mark_sent(record.post_id)

    logger.info("Pipeline completado")


if __name__ == "__main__":
    run()
