# scrapers/tecnoempleo.py — scraper propio de Tecnoempleo

import hashlib
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

TECNOEMPLEO_SEARCH_URL = "https://www.tecnoempleo.com/busqueda-empleo.php"
TECNOEMPLEO_KEYWORDS = ["RPA", "Python automatizacion", "AI developer"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def _make_id(url: str, title: str) -> str:
    raw = f"{url}{title}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def _parse_job_card(card, base_url: str) -> dict | None:
    """Extrae datos de una tarjeta de oferta del listado."""
    try:
        # Título y URL
        title_tag = card.select_one("h3.fs-5 a") or card.select_one("a.font-weight-bold")
        if not title_tag:
            return None
        title = title_tag.get_text(strip=True)
        relative_url = title_tag.get("href", "")
        url = base_url + relative_url if relative_url.startswith("/") else relative_url

        # Empresa
        company_tag = card.select_one("a.text-primary") or card.select_one("span.text-muted")
        company = company_tag.get_text(strip=True) if company_tag else ""

        # Localización
        location_tag = card.select_one("span.d-none.d-md-inline-block")
        location = location_tag.get_text(strip=True) if location_tag else "España"

        if not title or not url:
            return None

        return {
            "id": _make_id(url, title),
            "title": title,
            "company": company,
            "location": location,
            "source": "tecnoempleo",
            "url": url,
            "description": "",  # se rellena con fetch_description() si quieres
            "score": None,
            "notified": 0,
            "fecha_vista": datetime.now().isoformat(),
        }
    except Exception as e:
        print(f"[Tecnoempleo] Error parseando card: {e}")
        return None


def fetch_description(url: str) -> str:
    """Fetch opcional de la descripción completa de una oferta."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        desc_div = soup.select_one("div#detalle-oferta") or soup.select_one("div.job-description")
        return desc_div.get_text(separator="\n", strip=True) if desc_div else ""
    except Exception as e:
        print(f"[Tecnoempleo] Error fetching descripción {url}: {e}")
        return ""


def fetch_jobs(fetch_descriptions: bool = True) -> list[dict]:
    """
    Scrapes Tecnoempleo para cada keyword en TECNOEMPLEO_KEYWORDS.
    fetch_descriptions=True hace una request adicional por oferta (más lento pero mejor matching).
    """
    seen_ids = set()
    results = []

    for keyword in TECNOEMPLEO_KEYWORDS:
        print(f"[Tecnoempleo] Buscando: '{keyword}'...")
        params = {
            "te": keyword,
            "tp": "",
            "pr": "",
            "po": 1,
        }

        try:
            resp = requests.get(
                TECNOEMPLEO_SEARCH_URL,
                params=params,
                headers=HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
        except Exception as e:
            print(f"[Tecnoempleo] Error en request '{keyword}': {e}")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("div.p-3.border.rounded") or soup.select("div.col-10")

        if not cards:
            print(f"[Tecnoempleo] Sin tarjetas para '{keyword}' — revisar selectores CSS")
            continue

        for card in cards:
            job = _parse_job_card(card, TECNOEMPLEO_SEARCH_URL.split("/busqueda")[0])
            if not job or job["id"] in seen_ids:
                continue
            seen_ids.add(job["id"])

            if fetch_descriptions and job["url"]:
                job["description"] = fetch_description(job["url"])
                time.sleep(1)  # respetar rate limit

            results.append(job)

        print(f"[Tecnoempleo] '{keyword}' → {len(results)} acumuladas")
        time.sleep(2)

    print(f"[Tecnoempleo] Total: {len(results)} ofertas")
    return results
