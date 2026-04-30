import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

# ── Descarga parquets desde HF si es necesario ──
import os
from pathlib import Path as P

hf_token   = st.secrets.get("HF_TOKEN")
hf_dataset = st.secrets.get("HF_DATASET")

if hf_token and hf_dataset:
    cache_dir = P("/tmp/gkmobile_parquets")
    if not cache_dir.exists() or not any(cache_dir.rglob("*.parquet")):
        with st.spinner("Descargando datos... esto puede tardar unos minutos."):
            from huggingface_hub import snapshot_download
            snapshot_download(
                repo_id=hf_dataset,
                repo_type="dataset",
                token=hf_token,
                local_dir=str(cache_dir),
                ignore_patterns=["*.md", ".gitattributes"],
            )
    os.environ["PARQUET_DIR"] = str(cache_dir)

from app.auth import check_password
check_password()
# ... resto del código

import path_setup
import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.auth import check_password
check_password()

pg = st.navigation([
    st.Page("pages/1_Operacion_Global.py", title="Operación Global", icon="📊", default=True),
    st.Page("pages/2_Monitor_Geo.py",      title="Monitor Geo",      icon="📍"),
    st.Page("pages/3_Inicio_Eatics.py",    title="Eatics Dashboard", icon="🛒"),
    st.Page("pages/4_Procesa_SellOut.py",    title="Procesa Sell Out", icon="📦"),
])

pg.run()
