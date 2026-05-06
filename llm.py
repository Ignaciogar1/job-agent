# llm.py — análisis de ofertas con Gemini Flash

import json
import os
import base64
from google import genai

CONFIG_PATH = "user_config.json"


def _load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_client():
    config = _load_config()
    api_key = config.get("gemini_api_key")
    if not api_key:
        raise ValueError("No hay gemini_api_key en user_config.json")
    return genai.Client(api_key=api_key)


def analyze_job(job: dict, profile_text: str) -> dict:
    client = _get_client()

    prompt = f"""
Eres un asistente de búsqueda de empleo. Analiza si esta oferta es adecuada para el candidato.

PERFIL DEL CANDIDATO:
{profile_text}

OFERTA:
Título: {job.get('title', '')}
Empresa: {job.get('company', '')}
Ubicación: {job.get('location', '')}
Descripción: {job.get('description', '')[:2000]}

INSTRUCCIONES:
- El candidato busca posición junior o mid-level (0-4 años de experiencia)
- Valora si sus habilidades en RPA, Python y automatización encajan
- Sé directo y conciso

Responde ÚNICAMENTE con este JSON, sin texto adicional ni backticks:
{{
    "relevant": true o false,
    "reason": "1-2 frases explicando por qué es o no relevante",
    "missing": "qué habilidades le faltan o 'ninguna' si encaja bien",
    "highlights": "qué puntos fuertes del candidato encajan con esta oferta"
}}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        text = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "relevant": True,
            "reason": "No se pudo parsear respuesta de Gemini",
            "missing": "",
            "highlights": ""
        }
    except Exception as e:
        print(f"[LLM] Error analizando oferta '{job.get('title')}': {e}")
        return {
            "relevant": True,
            "reason": f"Error: {e}",
            "missing": "",
            "highlights": ""
        }


def analyze_jobs_batch(jobs: list[dict], profile_text: str) -> list[dict]:
    import time
    print(f"[LLM] Analizando {len(jobs)} ofertas con Gemini...")
    print(f"[LLM] Ritmo: 1 llamada cada 5s para respetar rate limit gratuito")
    results = []

    for i, job in enumerate(jobs):
        print(f"  [{i+1}/{len(jobs)}] {job['title']} — {job.get('company', '')}")
        analysis = analyze_job(job, profile_text)

        if analysis.get("relevant"):
            job["llm_analysis"] = analysis
            results.append(job)
            print(f"    ✓ Relevante: {analysis.get('reason', '')}")
        else:
            print(f"    ✗ Descartada: {analysis.get('reason', '')}")

        if i < len(jobs) - 1:
            time.sleep(5)

    print(f"[LLM] {len(results)}/{len(jobs)} ofertas aprobadas por Gemini")
    return results


def generate_profile_from_cv(cv_path: str) -> tuple[str, list[str]]:
    client = _get_client()

    with open(cv_path, "rb") as f:
        cv_bytes = f.read()
    cv_b64 = base64.b64encode(cv_bytes).decode("utf-8")

    prompt = """
Analiza este CV y genera dos cosas:

1. Un perfil profesional en texto plano (máximo 200 palabras) que resuma:
   - Experiencia y habilidades técnicas principales
   - Tecnologías que domina
   - Tipo de roles que busca
   - Nivel de experiencia
   - Idiomas y ubicación

2. Entre 4 y 6 términos de búsqueda para encontrar ofertas relevantes en España.
   Deben ser términos reales que aparecen en portales de empleo españoles.

Responde ÚNICAMENTE con este JSON, sin texto adicional ni backticks:
{
    "profile": "texto del perfil aquí",
    "search_terms": ["término 1", "término 2", "término 3", "término 4"]
}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                {
                    "parts": [
                        {"inline_data": {"mime_type": "application/pdf", "data": cv_b64}},
                        {"text": prompt}
                    ]
                }
            ]
        )
        text = response.text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        return data["profile"], data["search_terms"]
    except Exception as e:
        raise RuntimeError(f"Error procesando CV con Gemini: {e}")
