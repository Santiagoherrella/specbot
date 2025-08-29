# app.py
import time
import base64
from pathlib import Path
import streamlit as st

# ====== TUS IMPORTS EXISTENTES ======
from corelogic import get_llm
from utils import extract_text_from_pdf_bytes, resumen_documento
from promots import get_prompt_summary_str
# ====================================

# -----------------------------
# CONFIGURACIÓN BÁSICA PÁGINA
# -----------------------------
ASSETS = Path("assets")
HERO_PATH = ASSETS / "banner.png"   # opcional; si no existe, usa color corporativo
LOGO =  ASSETS / "logo.png" 
CORP = "#0f6db4"

st.set_page_config(
    page_title="Analizador MultiPDF IA",
    page_icon=LOGO,
    
    layout="wide",
)

# -----------------------------
# UTILIDADES DISEÑO
# -----------------------------
def _b64(path: Path):
    if path.exists():
        return base64.b64encode(path.read_bytes()).decode("utf-8")
    return ""

def apply_skin():
    """
    Tema adaptable Light/Dark (sin forzarlo), header fijo,
    subheaders en blanco y st.info en blanco con buen contraste.
    Sin 'cards'; solo pad-block para conservar espacios.
    """
    hero_bg = _b64(HERO_PATH)

    st.markdown(
        f"""
        <style>
        /* Tipografía global */
        * {{ font-family: Verdana, sans-serif !important; }}

        /* Variables por defecto (modo claro) */
        :root {{
          --corp: {CORP};
          --text: #0f172a;           /* texto principal */
          --bg:   #f8fafc;           /* fondo general */
          --surface: #ffffff;        /* superficies claras */
          --muted: #475569;          /* texto secundario */
          --border: #e5e7eb;         /* bordes suaves */
        }}

        /* Overrides modo oscuro */
        .stApp[data-theme="dark"] :root {{
          --text:   #e5e7eb;
          --bg:     #0b1220;
          --surface:#0f1523;         /* NO todo blanco; buen contraste */
          --muted:  #cbd5e1;
          --border: #1f2937;
        }}

        .stApp {{ background: var(--bg); color: var(--text); }}

        /* HERO (sin transparencia) */
        .hero {{
          position: relative;
          margin: 12px 0 18px 0;
          border-radius: 16px;
          overflow: hidden;
          min-height: 100px;
          box-shadow: 0 6px 18px rgba(0,0,0,.08);
          background: var(--corp);
        }}
        .hero-bg {{
          position:absolute; inset:0;
          {"background: url('data:image/jpg;base64,"+hero_bg+"') center/cover no-repeat;" if hero_bg else "background: var(--corp);"}
        }}
        .hero-content {{
          position: relative; z-index: 1; color: #fff;
          display:flex; align-items:center; gap:10px; padding:14px 18px;
        }}
        /* Icono documento (emoji) — AJUSTA AQUÍ EL TAMAÑO */
        .doc-emoji {{
          font-size: 2.4rem !important;   /* <-- sube/baja este valor */
          line-height: 1;
          margin-right: 8px;
        }}
        /* Título header — AJUSTA AQUÍ EL TAMAÑO */
        .hero-title {{
          margin: 0 !important;
          font-weight: 700 !important;
          line-height: 1.05 !important;
          font-size: 2rem !important;     /* <-- sube/baja este valor */
        }}
        .hero-sub {{
          margin: 4px 0 0 0;
          font-size: .82rem;
          opacity: .95;
        }}

        /* Subheaders estilo “chip” blanco (también en dark) */
        .section-title {{
          display: inline-block;
          padding: 6px 12px;
          background: #ffffff;       /* blanco siempre */
          color: #0f172a;            /* texto oscuro para legibilidad */
          border-left: 6px solid var(--corp);
          border-radius: 10px;
          font-size: 0.98rem; 
          font-weight: 700; 
          margin: 18px 0 10px 0;
        }}

