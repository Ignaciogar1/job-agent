# matcher.py — similitud coseno entre perfil y ofertas

import numpy as np
from embeddings import embed, embed_profile
from db import get_jobs_without_score, update_score
from filters import apply_keyword_filter
import json
import os

SIMILARITY_THRESHOLD = 0.45  # valor por defecto si no hay user_config.json
CONFIG_PATH = "user_config.json"


def get_threshold() -> float:
    """Lee el umbral desde user_config.json si existe, si no usa el de config.py."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("similarity_threshold", SIMILARITY_THRESHOLD)
    return SIMILARITY_THRESHOLD


def cosine_similarity(vec_a, vec_b) -> float:
    a = np.array(vec_a)
    b = np.array(vec_b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def score_jobs() -> dict:
    jobs = get_jobs_without_score()

    if not jobs:
        print("[Matcher] No hay ofertas pendientes de scoring.")
        return {"total": 0, "above_threshold": 0, "below_threshold": 0, "excluded": 0}

    print(f"[Matcher] {len(jobs)} ofertas pendientes de scoring.")

    # --- Filtro de keywords ---
    print("[Filtro] Aplicando filtro de keywords...")
    jobs_filtered, excluded = apply_keyword_filter(jobs)
    print(f"[Filtro] {excluded} excluidas | {len(jobs_filtered)} pasan al scoring")

    # Marcar excluidas con score 0 en BD para no reprocesarlas
    filtered_ids = {j["id"] for j in jobs_filtered}
    for job in jobs:
        if job["id"] not in filtered_ids:
            update_score(job["id"], 0.0)

    if not jobs_filtered:
        print("[Matcher] Ninguna oferta pasó el filtro de keywords.")
        return {"total": len(jobs), "above_threshold": 0, "below_threshold": 0, "excluded": excluded}

    # --- Embeddings + Matching ---
    threshold = get_threshold()
    print(f"[Matcher] Calculando similitud (umbral: {threshold})...")
    _, profile_vector = embed_profile()

    above = 0
    below = 0

    for i, job in enumerate(jobs_filtered):
        job_text = f"{job['title']} {job['company']} {job['description']}".strip()

        if not job_text:
            update_score(job["id"], 0.0)
            below += 1
            continue

        job_vector = embed(job_text)
        score = cosine_similarity(profile_vector, job_vector)
        update_score(job["id"], round(score, 4))

        if score >= threshold:
            above += 1
            print(f"  ✓ [{score:.3f}] {job['title']} — {job.get('company', '')}")
        else:
            below += 1

        if (i + 1) % 10 == 0:
            print(f"  ... {i + 1}/{len(jobs_filtered)} procesadas")

    print(f"[Matcher] Completado: {above} relevantes | {below} descartadas | {excluded} excluidas por keywords")
    return {"total": len(jobs), "above_threshold": above, "below_threshold": below, "excluded": excluded}
