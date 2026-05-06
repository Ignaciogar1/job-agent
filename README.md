# Job Agent 🤖

Monitoriza ofertas en España, las compara con mi perfil usando embeddings semánticos, filtra las que no encajan (senior, lead, director...) y me manda las relevantes directamente al móvil por Telegram. Lo construí también como forma práctica de meterme en agentic AI — nada mejor que aprender construyendo algo que te soluciona un problema real.

---

## ¿Cómo funciona?

El agente corre un pipeline de 4 fases:

```
Scraping → Filtro keywords → Embeddings + Matching → Telegram
                                      ↓
                              LLM (Gemini) opcional
```

**Fase 1 — Scraping**
Obtiene ofertas de Tecnoempleo según los términos configurados y las guarda en SQLite. Si una oferta ya existe en la BD no se vuelve a procesar.

**Fase 2 — Filtro + Embeddings**
Primero descarta ofertas por keywords de seniority (senior, lead, director...). Las que pasan se vectorizan con `sentence-transformers` y se comparan con mi perfil mediante similitud coseno. Solo las que superan el umbral configurado siguen adelante.

**Fase 3 — LLM (opcional)**
Si Gemini está activado, analiza cada oferta candidata y decide si encaja con el perfil del candidato, explicando los puntos fuertes y lo que falta. Activable desde `user_config.json` sin tocar el código.

**Fase 4 — Telegram**
Manda una notificación por cada oferta relevante al chat configurado, con título, empresa, score de similitud, URL y el análisis de Gemini si está activo.

---

## Stack técnico

| Componente | Tecnología |
|---|---|
| Scraping | `requests` + `BeautifulSoup` |
| Base de datos | SQLite (`sqlite3`) |
| Embeddings | `sentence-transformers` — `paraphrase-multilingual-MiniLM-L12-v2` |
| LLM | Gemini 2.0 Flash (`google-genai`) |
| Notificaciones | Telegram Bot API |
| Lenguaje | Python 3.11+ |

---

## Instalación

```bash
git clone https://github.com/tu-usuario/job_agent.git
cd job_agent

python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt
```

---

## Configuración

Ejecuta el wizard:

```bash
python setup.py
```

Te pregunta el nivel de experiencia, umbral de similitud y términos de búsqueda. Genera el `user_config.json` con todo.

Luego añade tus credenciales en ese mismo archivo:

```json
{
  "gemini_api_key": "TU_API_KEY",
  "telegram_bot_token": "TU_BOT_TOKEN",
  "telegram_chat_id": "TU_CHAT_ID"
}
```

Y edita `profile.txt` con tu perfil profesional — ese texto es el que se vectoriza para comparar contra las ofertas.

### Gemini está desactivado por defecto

Para no depender de la API para ejecutar el agente, Gemini va desactivado por defecto. Si quieres activarlo, añade esto a `user_config.json`:

```json
"use_llm": true
```

Con esto activo, cada oferta que supere el umbral pasa por Gemini antes de notificarse. Filtra falsos positivos y te explica exactamente por qué encaja (o no) con tu perfil.

---

## Uso

```bash
python main.py
```

Ejecuta el pipeline completo y manda los resultados a Telegram. Las ofertas notificadas quedan marcadas en la BD y no se repiten en la siguiente ejecución.

---

## Estructura del proyecto

```
job_agent/
├── main.py              # Orquestador principal
├── config.py            # Constantes técnicas
├── db.py                # Capa de persistencia SQLite
├── embeddings.py        # Carga del modelo y vectorización
├── matcher.py           # Similitud coseno y filtrado
├── filters.py           # Filtro de keywords de exclusión
├── llm.py               # Integración con Gemini Flash
├── notifier.py          # Bot de Telegram
├── setup.py             # Wizard de configuración inicial
├── profile.txt          # Perfil profesional del usuario
├── requirements.txt
├── scrapers/
│   └── tecnoempleo.py   # Scraper de Tecnoempleo
└── data/
    └── jobs.db          # Base de datos local
```
