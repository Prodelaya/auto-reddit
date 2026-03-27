"""Orquestador del proceso diario: conecta todos los módulos y ejecuta el flujo completo."""

import logging

from auto_reddit.config.settings import settings
from auto_reddit.reddit.client import collect_candidates

logger = logging.getLogger(__name__)


def run() -> None:
    """Entry point del pipeline diario."""
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )

    logger.info("Iniciando pipeline auto-reddit")

    # Change 1: recoger candidatos de r/Odoo (ventana 7 días)
    candidates = collect_candidates(settings)
    logger.info("Candidatos recogidos: %d", len(candidates))

    # Change 2 (pendiente): filtro de memoria, exclusiones y recorte a 8
    # candidates = filter_candidates(candidates, settings)

    # Change 3 (pendiente): enriquecer con comentarios
    # candidates = enrich_with_comments(candidates, settings)

    logger.info("Pipeline completado")


if __name__ == "__main__":
    run()
