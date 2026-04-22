import streamlit as st
import hmac

def check_password():
    if st.session_state.get("authenticated"):
        return True

    st.title("GKMobile")
    st.subheader("Iniciar sesión")

    with st.form("login"):
        usuario  = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submit   = st.form_submit_button("Entrar")

    if submit:
        usuario_ok  = hmac.compare_digest(usuario,  st.secrets["LOGIN_USER"])
        password_ok = hmac.compare_digest(password, st.secrets["LOGIN_PASSWORD"])

        if usuario_ok and password_ok:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

    st.stop()