# notifier.py — envío de notificaciones por Telegram

import json
import requests

CONFIG_PATH = "user_config.json"


def _load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_credentials() -> tuple[str, str]:
    config = _load_config()
    token = config.get("telegram_bot_token")
    chat_id = config.get("telegram_chat_id")
    if not token or not chat_id:
        raise ValueError("Faltan telegram_bot_token o telegram_chat_id en user_config.json")
    return token, str(chat_id)


def send_message(text: str):
    """Envía un mensaje de texto al chat configurado."""
    token, chat_id = _get_credentials()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()


def notify_jobs(jobs: list[dict]):
    """
    Envía una notificación por cada oferta relevante.
    jobs es la lista de ofertas que pasaron todos los filtros.
    """
    if not jobs:
        print("[Telegram] No hay ofertas para notificar.")
        return

    # Mensaje de cabecera
    send_message(f"🤖 <b>Job Agent</b> — {len(jobs)} ofertas relevantes encontradas")

    for job in jobs:
        score = job.get("score", 0)
        title = job.get("title", "")
        company = job.get("company", "")
        location = job.get("location", "")
        url = job.get("url", "")

        # Si Gemini analizó la oferta, incluimos su análisis
        analysis = job.get("llm_analysis", {})
        reason = analysis.get("reason", "")
        highlights = analysis.get("highlights", "")
        missing = analysis.get("missing", "")

        # Construcción del mensaje
        lines = [
            f"💼 <b>{title}</b>",
            f"🏢 {company} — {location}",
            f"📊 Score: {score:.2f}",
        ]

        if reason:
            lines.append(f"✅ {reason}")
        if highlights:
            lines.append(f"⭐ {highlights}")
        if missing and missing.lower() != "ninguna":
            lines.append(f"⚠️ Falta: {missing}")

        lines.append(f'🔗 <a href="{url}">Ver oferta</a>')

        message = "\n".join(lines)

        try:
            send_message(message)
            print(f"[Telegram] ✓ Enviada: {title}")
        except Exception as e:
            print(f"[Telegram] Error enviando '{title}': {e}")

    print(f"[Telegram] {len(jobs)} notificaciones enviadas.")


def notify_summary(stats: dict):
    """Mensaje de resumen al final de la ejecución."""
    msg = (
        f"📋 <b>Resumen ejecución</b>\n"
        f"Total en BD: {stats.get('total', 0)}\n"
        f"Notificadas hoy: {stats.get('notified', 0)}"
    )
    try:
        send_message(msg)
    except Exception as e:
        print(f"[Telegram] Error enviando resumen: {e}")
