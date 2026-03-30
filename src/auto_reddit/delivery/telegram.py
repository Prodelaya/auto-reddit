"""Cliente Telegram: recibe oportunidades evaluadas, formatea mensajes y los envía al canal configurado."""

from __future__ import annotations

import logging

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

_TELEGRAM_API_BASE = "https://api.telegram.org"


@retry(
    retry=retry_if_exception_type(httpx.HTTPError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _post_message(url: str, payload: dict) -> httpx.Response:
    """POST a message to Telegram with retry on transient HTTP errors."""
    return httpx.post(url, json=payload, timeout=15)


def send_message(token: str, chat_id: str, text: str) -> bool:
    """Envía un mensaje de texto a Telegram con parse_mode=HTML.

    Args:
        token: Bot token de Telegram (sin el prefijo ``bot``).
        chat_id: ID del chat o canal destino.
        text: Texto HTML del mensaje.

    Returns:
        ``True`` solo cuando la respuesta HTTP es 200 y el cuerpo contiene
        ``"ok": true``. ``False`` en cualquier otro caso (error de red,
        status != 200, ``ok`` != true, JSON malformado).
    """
    url = f"{_TELEGRAM_API_BASE}/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }

    try:
        response = _post_message(url, payload)
    except httpx.HTTPError as exc:
        logger.warning("Telegram HTTP error after retries: %s", exc)
        return False

    if response.status_code != 200:
        logger.warning(
            "Telegram respondió con status %d: %s",
            response.status_code,
            response.text[:200],
        )
        return False

    try:
        body = response.json()
    except Exception as exc:
        logger.warning("Telegram response JSON parse error: %s", exc)
        return False

    ok = body.get("ok") is True
    if not ok:
        logger.warning("Telegram ok=false: %s", body.get("description", ""))
    return ok
