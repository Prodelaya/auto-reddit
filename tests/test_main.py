"""Tests unitarios para main.py.

Cubre:
- 4.1: Guardia de fin de semana — Sábado y Domingo omiten el pipeline sin efectos secundarios
- 4.1: Días laborables (Lunes–Viernes) continúan con el pipeline normal
"""

from __future__ import annotations

import datetime
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# 4.1: Weekend guard (Spec scenarios: Weekend run is skipped cleanly / Weekday proceeds)
# ---------------------------------------------------------------------------


class TestWeekendGuard:
    """Spec scenarios para la guardia de fin de semana en main.run()."""

    def _patch_pipeline(self):
        """Contexto de parches para aislar el pipeline de efectos secundarios reales."""
        return [
            patch("auto_reddit.main.settings"),
            patch("auto_reddit.main.CandidateStore"),
            patch("auto_reddit.main.collect_candidates", return_value=[]),
            patch("auto_reddit.main.fetch_thread_contexts", return_value=[]),
            patch("auto_reddit.main.evaluate_batch", return_value=[]),
            patch("auto_reddit.main.deliver_daily"),
        ]

    @pytest.mark.parametrize(
        "weekday,name",
        [
            (5, "Saturday"),
            (6, "Sunday"),
        ],
    )
    def test_weekend_run_returns_without_pipeline_side_effects(self, weekday, name):
        """
        Spec scenario: Weekend run is skipped cleanly.
        Un run de sábado o domingo termina antes de colección, evaluación y entrega.
        """
        from auto_reddit.main import run

        fixed_date = datetime.date(2026, 3, 28)  # Sábado
        # Build a date with the target weekday
        # weekday() 5=Sat, 6=Sun
        # Use a known Saturday: 2026-03-28 (weekday=5) and Sunday 2026-03-29 (weekday=6)
        if weekday == 5:
            target_date = datetime.date(2026, 3, 28)  # Saturday
        else:
            target_date = datetime.date(2026, 3, 29)  # Sunday

        with (
            patch("auto_reddit.main.datetime") as mock_dt,
            patch("auto_reddit.main.CandidateStore") as mock_store_cls,
            patch("auto_reddit.main.collect_candidates") as mock_collect,
            patch("auto_reddit.main.fetch_thread_contexts") as mock_fetch,
            patch("auto_reddit.main.evaluate_batch") as mock_eval,
            patch("auto_reddit.main.deliver_daily") as mock_deliver,
        ):
            mock_dt.date.today.return_value = target_date

            run()

        # Ningún efecto secundario debe ocurrir
        mock_store_cls.assert_not_called()
        mock_collect.assert_not_called()
        mock_fetch.assert_not_called()
        mock_eval.assert_not_called()
        mock_deliver.assert_not_called()

    @pytest.mark.parametrize(
        "weekday,target_date",
        [
            (0, datetime.date(2026, 3, 23)),  # Monday
            (1, datetime.date(2026, 3, 24)),  # Tuesday
            (2, datetime.date(2026, 3, 25)),  # Wednesday
            (3, datetime.date(2026, 3, 26)),  # Thursday
            (4, datetime.date(2026, 3, 27)),  # Friday
        ],
    )
    def test_weekday_run_proceeds_to_pipeline(self, weekday, target_date):
        """
        Spec scenario: Weekday run proceeds normally.
        De lunes a viernes, la guardia pasa y el pipeline se ejecuta.
        """
        from auto_reddit.main import run

        mock_settings = MagicMock()
        mock_settings.db_path = ":memory:"
        mock_settings.daily_review_limit = 8

        mock_store = MagicMock()
        mock_store.get_decided_post_ids.return_value = set()
        mock_store.get_pending_deliveries.return_value = []

        with (
            patch("auto_reddit.main.datetime") as mock_dt,
            patch("auto_reddit.main.settings", mock_settings),
            patch("auto_reddit.main.CandidateStore", return_value=mock_store),
            patch(
                "auto_reddit.main.collect_candidates", return_value=[]
            ) as mock_collect,
            patch("auto_reddit.main.fetch_thread_contexts", return_value=[]),
            patch("auto_reddit.main.evaluate_batch", return_value=[]),
            patch(
                "auto_reddit.main.deliver_daily",
                return_value=MagicMock(
                    total_selected=0,
                    retries=0,
                    new=0,
                    sent_ok=0,
                    sent_failed=0,
                    summary_sent=True,
                    expired_skipped=0,
                ),
            ),
        ):
            mock_dt.date.today.return_value = target_date

            run()

        # collect_candidates debe haber sido llamado (el pipeline arrancó)
        mock_collect.assert_called_once()
