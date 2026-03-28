"""Tests para delivery/telegram.py.

Cubre:
- 4.3: send_message() éxito (200 + ok=true → True)
- 4.3: send_message() fallo de status (non-200 → False)
- 4.3: send_message() JSON malformado → False
- 4.3: send_message() ok=false → False
- 4.3: parse_mode=HTML incluido en el payload de la petición
- 4.3: excepción de red → False
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from auto_reddit.delivery.telegram import send_message


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_response(
    status_code: int, json_data: dict | None, raise_json: bool = False
) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    if raise_json:
        response.json.side_effect = ValueError("invalid JSON")
    elif json_data is not None:
        response.json.return_value = json_data
    response.text = str(json_data)
    return response


# ---------------------------------------------------------------------------
# 4.3: Éxito
# ---------------------------------------------------------------------------


class TestSendMessageSuccess:
    def test_200_ok_true_returns_true(self):
        mock_resp = _mock_response(200, {"ok": True, "result": {"message_id": 42}})
        with patch(
            "auto_reddit.delivery.telegram.httpx.post", return_value=mock_resp
        ) as mock_post:
            result = send_message("BOT_TOKEN", "CHAT_ID", "Hello <b>world</b>")
        assert result is True

    def test_parse_mode_html_in_payload(self):
        """El payload de la petición debe incluir parse_mode=HTML."""
        mock_resp = _mock_response(200, {"ok": True})
        with patch(
            "auto_reddit.delivery.telegram.httpx.post", return_value=mock_resp
        ) as mock_post:
            send_message("TOKEN", "CHAT", "text")
        _, kwargs = mock_post.call_args
        # httpx.post llamado con json=payload
        payload = kwargs.get("json") or mock_post.call_args[1].get("json")
        assert payload is not None
        assert payload.get("parse_mode") == "HTML"

    def test_chat_id_and_text_in_payload(self):
        """chat_id y text deben estar en el payload."""
        mock_resp = _mock_response(200, {"ok": True})
        with patch(
            "auto_reddit.delivery.telegram.httpx.post", return_value=mock_resp
        ) as mock_post:
            send_message("TOKEN", "MY_CHAT_ID", "My message text")
        _, kwargs = mock_post.call_args
        payload = kwargs.get("json") or mock_post.call_args[1].get("json")
        assert payload["chat_id"] == "MY_CHAT_ID"
        assert payload["text"] == "My message text"

    def test_url_contains_bot_token(self):
        """La URL de la petición debe incluir el token del bot."""
        mock_resp = _mock_response(200, {"ok": True})
        with patch(
            "auto_reddit.delivery.telegram.httpx.post", return_value=mock_resp
        ) as mock_post:
            send_message("MY_SECRET_TOKEN", "CHAT", "text")
        url_arg = mock_post.call_args[0][0]
        assert "MY_SECRET_TOKEN" in url_arg
        assert "sendMessage" in url_arg


# ---------------------------------------------------------------------------
# 4.3: Fallo de status HTTP
# ---------------------------------------------------------------------------


class TestSendMessageHttpFailure:
    def test_non_200_returns_false(self):
        mock_resp = _mock_response(400, {"ok": False, "description": "Bad Request"})
        with patch("auto_reddit.delivery.telegram.httpx.post", return_value=mock_resp):
            result = send_message("TOKEN", "CHAT", "text")
        assert result is False

    def test_500_returns_false(self):
        mock_resp = _mock_response(500, {"ok": False})
        with patch("auto_reddit.delivery.telegram.httpx.post", return_value=mock_resp):
            result = send_message("TOKEN", "CHAT", "text")
        assert result is False

    def test_401_returns_false(self):
        mock_resp = _mock_response(401, {"ok": False, "description": "Unauthorized"})
        with patch("auto_reddit.delivery.telegram.httpx.post", return_value=mock_resp):
            result = send_message("TOKEN", "CHAT", "text")
        assert result is False


# ---------------------------------------------------------------------------
# 4.3: JSON malformado
# ---------------------------------------------------------------------------


class TestSendMessageMalformedJSON:
    def test_malformed_json_response_returns_false(self):
        mock_resp = _mock_response(200, None, raise_json=True)
        with patch("auto_reddit.delivery.telegram.httpx.post", return_value=mock_resp):
            result = send_message("TOKEN", "CHAT", "text")
        assert result is False


# ---------------------------------------------------------------------------
# 4.3: ok=false en body
# ---------------------------------------------------------------------------


class TestSendMessageOkFalse:
    def test_200_ok_false_returns_false(self):
        mock_resp = _mock_response(200, {"ok": False, "description": "Flood control"})
        with patch("auto_reddit.delivery.telegram.httpx.post", return_value=mock_resp):
            result = send_message("TOKEN", "CHAT", "text")
        assert result is False

    def test_200_missing_ok_field_returns_false(self):
        """Body sin campo 'ok' debe devolver False (ok no es True)."""
        mock_resp = _mock_response(200, {"result": "something"})
        with patch("auto_reddit.delivery.telegram.httpx.post", return_value=mock_resp):
            result = send_message("TOKEN", "CHAT", "text")
        assert result is False


# ---------------------------------------------------------------------------
# 4.3: Excepción de red
# ---------------------------------------------------------------------------


class TestSendMessageNetworkError:
    def test_http_error_returns_false(self):
        import httpx as httpx_module

        with patch(
            "auto_reddit.delivery.telegram.httpx.post",
            side_effect=httpx_module.HTTPError("Connection refused"),
        ):
            result = send_message("TOKEN", "CHAT", "text")
        assert result is False

    def test_connect_error_returns_false(self):
        import httpx as httpx_module

        with patch(
            "auto_reddit.delivery.telegram.httpx.post",
            side_effect=httpx_module.ConnectError("Cannot connect"),
        ):
            result = send_message("TOKEN", "CHAT", "text")
        assert result is False
