import streamlit as st

THEME_CSS = """
<style>
/* Placeholder da Sprint 1.
   Na próxima etapa vamos mover todo o CSS existente do app.py para cá. */
</style>
"""

def apply_theme() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)