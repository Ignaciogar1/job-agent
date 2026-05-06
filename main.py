# main.py — orquestador principal
# Fases: scraping + embeddings + matching + LLM + Telegram

from db import init_db, insert_job, job_exists, stats, get_unnotified_above_threshold, mark_as_notified
from scrapers.tecnoempleo import fetch_jobs as fetch_tecnoempleo
from matcher import score_jobs
from embeddings import load_profile
from llm import analyze_jobs_batch
from notifier import notify_jobs, notify_summary
import json
import os

CONFIG_PATH = "user_config.json"


def validate_config() -> bool:
    """
    Valida que user_config.json existe y tiene los campos mínimos necesarios.
    Para el agente antes de ejecutar nada.
    """
    if not os.path.exists(CONFIG_PATH):
        print("=" * 50)
        print("[ERROR] No se encontró user_config.json")
        print("Ejecuta primero: python setup.py")
        print("=" * 50)
        return False

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError:
        print("=" * 50)
        print("[ERROR] user_config.json tiene un formato incorrecto.")
        print("Ejecuta de nuevo: python setup.py")
        print("=" * 50)
        return False

    # Campos obligatorios para que el agente funcione
    required = {
        "telegram_bot_token": "Token del bot de Telegram",
        "telegram_chat_id": "Chat ID de Telegram",
        "seniority_level": "Nivel de experiencia",
        "similarity_threshold": "Umbral de similitud",
    }

    missing = []
    for field, label in required.items():
        if not config.get(field):
            missing.append(f"  - {label} ({field})")

    if missing:
        print("=" * 50)
        print("[ERROR] Faltan campos en user_config.json:")
        for m in missing:
            print(m)
        print("\nEjecuta de nuevo: python setup.py")
        print("=" * 50)
        return False

    # Aviso si Gemini está activado pero no tiene API key
    if config.get("use_llm") and not config.get("gemini_api_key"):
        print("[AVISO] use_llm está activado pero falta gemini_api_key. Gemini se desactivará.")

    return True


def get_threshold() -> float:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("similarity_threshold", 0.45)
    return 0.45


def llm_enabled() -> bool:
    """Comprueba si Gemini está activado en user_config.json."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("use_llm", False) and bool(config.get("gemini_api_key"))
    return False


def run():
    print("=" * 50)
    print("JOB AGENT — Scraping + Matching + LLM + Telegram")
    print("=" * 50)

    init_db()
    print("[DB] Inicializada en data/jobs.db")

    all_jobs = []

    # --- Fase 1: Scraping ---
    try:
        tec_jobs = fetch_tecnoempleo(fetch_descriptions=True)
        all_jobs.extend(tec_jobs)
    except Exception as e:
        print(f"[ERROR] Tecnoempleo falló: {e}")

    nuevas = 0
    for job in all_jobs:
        if not job_exists(job["id"]):
            insert_job(job)
            nuevas += 1

    print(f"\n[RESUMEN SCRAPING] Nuevas: {nuevas} | Duplicadas: {len(all_jobs) - nuevas}")
    s = stats()
    print(f"[DB] Total: {s['total']} | Pendientes scoring: {s['pending_score']}")

    # --- Fase 2: Embeddings + Matching ---
    print("\n" + "=" * 50)
    score_jobs()

    # --- Fase 3: LLM ---
    print("\n" + "=" * 50)
    threshold = get_threshold()
    candidates = get_unnotified_above_threshold(threshold)

    if llm_enabled():
        print("[LLM] Gemini activado — analizando ofertas...")
        if not candidates:
            print("[LLM] No hay candidatas para analizar.")
            approved = []
        else:
            profile_text = load_profile()
            approved = analyze_jobs_batch(candidates, profile_text)
            for job in approved:
                mark_as_notified(job["id"])
    else:
        print("[LLM] Gemini desactivado — saltando análisis LLM.")
        approved = candidates

    # --- Fase 4: Telegram ---
    print("\n" + "=" * 50)
    if approved:
        notify_jobs(approved)
        if not llm_enabled():
            for job in approved:
                mark_as_notified(job["id"])
    else:
        print("[Telegram] No hay ofertas nuevas para notificar.")

    print("\n" + "=" * 50)
    s = stats()
    notify_summary(s)
    print(f"[FINAL] Total en BD: {s['total']} | Notificadas: {s['notified']}")
    print("=" * 50)


if __name__ == "__main__":
    if validate_config():
        run()
