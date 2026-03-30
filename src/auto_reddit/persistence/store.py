"""Store SQLite: guarda, consulta y purga registros de posts procesados con modelo de 3 estados y TTL."""

import sqlite3
import time

from auto_reddit.shared.contracts import PostDecision, PostRecord


class CandidateStore:
    """Almacén operativo SQLite para el estado de decisión de posts.

    Estados:
    - ``sent``: entregado con éxito a Telegram. Decisión final.
    - ``rejected``: rechazado por la IA. Decisión final. No re-entra al pipeline.
    - ``pending_delivery``: aceptado por la IA, esperando confirmación de Telegram.
      Estado transitorio operativo; se convierte en ``sent`` tras entrega exitosa.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def init_db(self) -> None:
        """Crea la tabla ``post_decisions`` si no existe."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS post_decisions (
                    post_id         TEXT PRIMARY KEY,
                    status          TEXT NOT NULL,
                    opportunity_data TEXT,
                    decided_at      INTEGER NOT NULL
                )
                """
            )
            conn.commit()

    def get_decided_post_ids(self) -> set[str]:
        """Devuelve los post_ids con estado ``sent`` o ``rejected`` (decisiones finales).

        Los posts en ``pending_delivery`` NO se incluyen: siguen siendo elegibles
        para el flujo de reintento sin re-evaluación IA.
        """
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT post_id FROM post_decisions WHERE status IN (?, ?)",
                (PostDecision.sent.value, PostDecision.rejected.value),
            ).fetchall()
        return {row[0] for row in rows}

    def save_rejected(self, post_id: str) -> None:
        """Persiste el post como ``rejected``. Upsert: actualiza si ya existía."""
        now = int(time.time())
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO post_decisions (post_id, status, opportunity_data, decided_at)
                VALUES (?, ?, NULL, ?)
                ON CONFLICT(post_id) DO UPDATE SET
                    status = excluded.status,
                    opportunity_data = excluded.opportunity_data,
                    decided_at = excluded.decided_at
                """,
                (post_id, PostDecision.rejected.value, now),
            )
            conn.commit()

    def save_pending_delivery(self, post_id: str, opportunity_data: str) -> None:
        """Persiste el post como ``pending_delivery`` con el resultado de evaluación IA.

        Upsert: si ya existía un registro (p. ej. un reintento), actualiza ``status``
        y ``opportunity_data`` pero preserva el ``decided_at`` original — la marca
        temporal de la primera decisión IA no debe variar en reintentos de entrega.
        """
        now = int(time.time())
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO post_decisions (post_id, status, opportunity_data, decided_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(post_id) DO UPDATE SET
                    status = excluded.status,
                    opportunity_data = excluded.opportunity_data
                """,
                (post_id, PostDecision.pending_delivery.value, opportunity_data, now),
            )
            conn.commit()

    def mark_sent(self, post_id: str) -> bool:
        """Marca el post como ``sent`` tras confirmación exitosa de Telegram.

        Sólo se debe llamar cuando Telegram confirma la entrega. No cambia
        ``opportunity_data`` ni crea un registro nuevo si no existía.

        Returns:
            ``True`` si se actualizó exactamente 1 fila (post existía).
            ``False`` si el post_id no existía en la base de datos.
        """
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "UPDATE post_decisions SET status = ? WHERE post_id = ?",
                (PostDecision.sent.value, post_id),
            )
            conn.commit()
        return cursor.rowcount == 1

    def purge_expired(self, post_ids: list[str]) -> int:
        """Elimina registros ``pending_delivery`` con TTL expirado.

        Llamado opcionalmente después de un ciclo de entrega para limpiar
        registros que el selector descartó por expiración de TTL y que ya no
        volverán a ser entregados.

        Args:
            post_ids: Lista de ``post_id`` de registros expirados a eliminar.

        Returns:
            Número de filas eliminadas.
        """
        if not post_ids:
            return 0
        placeholders = ",".join("?" for _ in post_ids)
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                f"DELETE FROM post_decisions WHERE post_id IN ({placeholders}) AND status = ?",
                (*post_ids, PostDecision.pending_delivery.value),
            )
            conn.commit()
        return cursor.rowcount

    def get_pending_deliveries(self) -> list[PostRecord]:
        """Devuelve todos los registros en estado ``pending_delivery``.

        Usado para reintentar entregas Telegram sin re-evaluar la IA.
        """
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT post_id, status, opportunity_data, decided_at
                FROM post_decisions
                WHERE status = ?
                """,
                (PostDecision.pending_delivery.value,),
            ).fetchall()
        return [
            PostRecord(
                post_id=row[0],
                status=PostDecision(row[1]),
                opportunity_data=row[2],
                decided_at=row[3],
            )
            for row in rows
        ]
