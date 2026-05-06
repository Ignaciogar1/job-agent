# filters.py — filtro de keywords sobre título y descripción de ofertas

import json
import os

CONFIG_PATH = "user_config.json"


def load_exclude_keywords() -> list[str]:
    if not os.path.exists(CONFIG_PATH):
        return []
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    return [k.lower() for k in config.get("exclude_keywords", [])]


def should_exclude(job: dict, exclude_keywords: list[str]) -> tuple[bool, str]:
    """
    Devuelve (True, keyword_encontrada) si la oferta debe excluirse.
    Devuelve (False, "") si pasa el filtro.
    Busca en título + descripción.
    """
    if not exclude_keywords:
        return False, ""

    title = (job.get("title") or "").lower()
    description = (job.get("description") or "").lower()
    text = f"{title} {description}"

    for keyword in exclude_keywords:
        if keyword in text:
            return True, keyword

    return False, ""


def apply_keyword_filter(jobs: list[dict]) -> tuple[list[dict], int]:
    """
    Filtra una lista de ofertas aplicando las keywords de exclusión.
    Devuelve (ofertas_que_pasan, número_excluidas).
    """
    exclude_keywords = load_exclude_keywords()

    if not exclude_keywords:
        return jobs, 0

    passed = []
    excluded = 0

    for job in jobs:
        is_excluded, keyword = should_exclude(job, exclude_keywords)
        if is_excluded:
            excluded += 1
            print(f"  ✗ Excluida por '{keyword}': {job['title']} — {job.get('company', '')}")
        else:
            passed.append(job)

    return passed, excluded
