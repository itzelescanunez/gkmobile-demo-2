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
