# embeddings.py — carga del modelo y generación de vectores

from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL, PROFILE_PATH

_model = None  # singleton, se carga una sola vez por ejecución


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"[Embeddings] Cargando modelo '{EMBEDDING_MODEL}'...")
        print("[Embeddings] Primera vez: descargando ~90MB, espera...")
        _model = SentenceTransformer(EMBEDDING_MODEL)
        print("[Embeddings] Modelo listo.")
    return _model


def embed(text: str):
    """Devuelve el vector embedding de un texto."""
    model = get_model()
    return model.encode(text, convert_to_tensor=False)


def load_profile() -> str:
    """Lee el perfil desde profile.txt."""
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()


def embed_profile() -> tuple[str, list]:
    """Devuelve (texto_perfil, vector_perfil)."""
    profile_text = load_profile()
    profile_vector = embed(profile_text)
    return profile_text, profile_vector
