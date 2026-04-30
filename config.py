from pathlib import Path
import os

BASE_DIR    = Path(__file__).parent
PARQUET_DIR = Path(os.getenv("PARQUET_DIR", str(BASE_DIR / "data/parquet")))

def _init_parquets():
    global PARQUET_DIR  # declarar al inicio de la función

    hf_token   = os.getenv("HF_TOKEN")
    hf_dataset = os.getenv("HF_DATASET")

    if not hf_token:
        try:
            import toml
            secrets_path = BASE_DIR / ".streamlit" / "secrets.toml"
            if secrets_path.exists():
                secrets = toml.load(str(secrets_path))
                hf_token   = secrets.get("HF_TOKEN")
                hf_dataset = secrets.get("HF_DATASET")
        except Exception:
            pass

    if not hf_token or not hf_dataset:
        return

    cache_dir = Path("/tmp/gkmobile_parquets")
    if cache_dir.exists() and any(cache_dir.rglob("*.parquet")):
        PARQUET_DIR = cache_dir
        return

    print("Descargando parquets desde Hugging Face...")
    from huggingface_hub import snapshot_download
    snapshot_download(
        repo_id=hf_dataset,
        repo_type="dataset",
        token=hf_token,
        local_dir=str(cache_dir),
        ignore_patterns=["*.md", ".gitattributes"],
    )
    print("✅ Parquets listos.")
    PARQUET_DIR = cache_dir

_init_parquets()

def parquet(nombre, cliente=None):
    if cliente:
        return str(PARQUET_DIR / cliente / f"{nombre}.parquet")
    for sub in ["global", "eatics", "procesa"]:
        path = PARQUET_DIR / sub / f"{nombre}.parquet"
        if path.exists():
            return str(path)
    raise FileNotFoundError(f"Parquet '{nombre}' no encontrado")

CLIENTES = {
    1:   "Philip Morris International",
    26:  "Procesa",
    102: "Castel",
    127: "Xiaomi",
    132: "Danone",
    141: "Clip",
    142: "Rabbit",
    149: "Eatics",
}

CADENAS_NORM = {
    "CHEDRAUI": "Chedraui",
    "SORIANA": "Soriana",
    "SAMS CLUB": "Sam''s Club",
    "SAMS": "Sam''s Club",
    "WALMART": "Walmart",
    "HEB": "HEB",
    "LA COMER": "La Comer",
    "COMERCIAL MEXICANA": "Comercial Mexicana",
    "ALSUPER": "Alsuper",
    "COSTCO": "Costco",
    "CASA LEY": "Casa Ley",
    "CALIMAX": "Calimax",
}

def sql_normalizar_cadena(col: str = "pv.cadena_str") -> str:
    cases = "\n".join([
        f"    WHEN UPPER(TRIM({col})) = '{k}' THEN '{v}'"
        for k, v in CADENAS_NORM.items()
    ])
    return f"""
        CASE
{cases}
            WHEN {col} IS NULL
              OR TRIM({col}) = ''
              OR UPPER(TRIM({col})) = 'NAN' THEN 'Sin cadena'
            ELSE TRIM({col})
        END
    """