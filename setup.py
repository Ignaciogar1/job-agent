# setup.py — configuración inicial del agente
# Ejecutar una sola vez: python setup.py

import json
import os

CONFIG_PATH = "user_config.json"

SENIORITY_KEYWORDS = {
    "1": {
        "level": "junior",
        "exclude_keywords": [
            "senior", "sr.", "lead", "principal", "staff",
            "head of", "director", "manager",
            "5 años", "6 años", "7 años", "8 años", "9 años", "10 años",
            "+5", "+6", "+7", "+8", "+4 years", "+5 years",
            "5 years", "6 years", "7 years"
        ]
    },
    "2": {
        "level": "mid",
        "exclude_keywords": [
            "senior", "sr.", "lead", "principal", "staff",
            "head of", "director", "manager",
            "7 años", "8 años", "9 años", "10 años",
            "+7", "+8", "+9", "+7 years", "+8 years"
        ]
    },
    "3": {
        "level": "senior",
        "exclude_keywords": []  # senior no excluye nada por seniority
    },
    "4": {
        "level": "any",
        "exclude_keywords": []
    }
}


def ask(question: str, valid_options: list = None, default: str = None, allow_empty: bool = False) -> str:
    while True:
        suffix = f" [{default}]" if default else ""
        response = input(f"{question}{suffix}: ").strip()
        if not response and default is not None and (default != "" or allow_empty):
            return default
        if not response and allow_empty:
            return ""
        if valid_options and response not in valid_options:
            print(f"  → Opción no válida. Elige entre: {', '.join(valid_options)}")
            continue
        if response:
            return response


def run_setup():
    print("\n" + "=" * 55)
    print("  JOB AGENT — Configuración inicial")
    print("=" * 55)
    print("Responde las siguientes preguntas para personalizar")
    print("el agente a tu perfil. Puedes repetir este wizard")
    print("en cualquier momento ejecutando: python setup.py\n")

    config = {}

    # --- Nivel de experiencia ---
    print("1) ¿Cuál es tu nivel de experiencia?")
    print("   1. Junior  (0-2 años)")
    print("   2. Mid     (2-4 años)")
    print("   3. Senior  (5+ años)")
    print("   4. Sin filtro de seniority")
    level_choice = ask("   Elige", valid_options=["1", "2", "3", "4"])
    seniority = SENIORITY_KEYWORDS[level_choice]
    config["seniority_level"] = seniority["level"]
    config["exclude_keywords"] = seniority["exclude_keywords"]

    # --- Umbral de similitud ---
    print("\n2) Umbral de similitud (0.40 - 0.80)")
    print("   Más alto = más estricto, menos ofertas notificadas")
    print("   Recomendado: 0.45 para empezar")
    while True:
        threshold_raw = ask("   Umbral", default="0.45")
        try:
            threshold = float(threshold_raw)
            if 0.30 <= threshold <= 0.90:
                config["similarity_threshold"] = threshold
                break
            print("  → Debe estar entre 0.30 y 0.90")
        except ValueError:
            print("  → Introduce un número decimal, ej: 0.45")

    # --- Términos de búsqueda ---
    print("\n3) Términos de búsqueda (separados por coma)")
    print("   Ejemplo: 'RPA developer, Python automatización, AI developer'")
    terms_raw = ask("   Términos", default="RPA developer, Python automatización, AI developer")
    config["search_terms"] = [t.strip() for t in terms_raw.split(",") if t.strip()]

    # --- Guardar ---
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 55)
    print(f"  Configuración guardada en {CONFIG_PATH}")
    print(f"  Nivel: {config['seniority_level']}")
    print(f"  Umbral: {config['similarity_threshold']}")
    print(f"  Keywords excluidas: {len(config['exclude_keywords'])}")
    print(f"  Términos de búsqueda: {len(config['search_terms'])}")
    print("=" * 55)
    print("\nYa puedes ejecutar: python main.py\n")


if __name__ == "__main__":
    run_setup()
