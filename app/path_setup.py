import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Verificar autenticación en todas las páginas
import streamlit as st

def require_auth():
    from app.auth import check_password
    check_password()