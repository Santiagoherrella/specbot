# app.py
#streamlit run app.py
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

        /* Bloques solo para ESPACIAR (sin card) */
        .pad-block {{
          padding: 14px;
          margin-bottom: 14px;
        }}

        /* Personalizar st.info para que sea BLANCO en ambos modos */
        .stAlert div[role="alert"] {{
          background: #ffffff !important;
          color: #0f172a !important;
          border: 1px solid var(--border) !important;
          border-radius: 12px !important;
        }}

        /* Inputs con bordes suaves y radio leve */
        .stTextInput > div > div > input,
        .stTextArea textarea,
        .stSelectbox > div > div,
        .stDateInput > div > div > input {{
          border-radius: 8px !important;
        }}

        /* Botones corporativos */
        .stButton > button {{
          background: var(--corp) !important;
          color:#fff !important;
          border-radius: 10px !important;
          border: none !important;
          font-weight:700 !important;
        }}
        .stButton > button:hover {{ filter: brightness(.95); }}
        
        /* Footer */
        .corp-footer {{
          position: fixed; left: 0; right: 0; bottom: 0;
          background: var(--corp); color: #fff;
          padding: 10px 16px; text-align: center; font-size: .9rem; z-index: 1000;
        }}

        

        </style>
        """,
        unsafe_allow_html=True,
    )

def hero_header(title="Analizador y Resumidor MultiPDF con IA", subtitle=None):
    if subtitle is None:
        subtitle = f"Hora actual: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-bg"></div>
          <div class="hero-content">
             <span class="doc-emoji" aria-hidden="true">📄</span>
             <div>
               <!-- OJO: usamos DIV (no h1) para que el tamaño respete tu CSS -->
               <div class="hero-title">{title}</div>
               <div class="hero-sub">{subtitle}</div>
             </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def section_title(txt: str):
    st.markdown(f'<div class="section-title">{txt}</div>', unsafe_allow_html=True)

def pad_start(): st.markdown('<div class="pad-block">', unsafe_allow_html=True)
def pad_end():   st.markdown('</div>', unsafe_allow_html=True)

def footer_corp():
    st.markdown('<div class="corp-footer">© MAGNETRON SAS 2025</div>', unsafe_allow_html=True)

# -----------------------------
# APLICAR DISEÑO
# -----------------------------
apply_skin()
hero_header()

# -----------------------------
# CACHE LLM
# -----------------------------
@st.cache_resource
def cached_llm():
    return get_llm()

RESUMEN_PROMPT = get_prompt_summary_str()
llm = cached_llm()

# -----------------------------
# ESTADO
# -----------------------------
if "multi_resumenes" not in st.session_state:
    st.session_state.multi_resumenes = {}

# -----------------------------
# UI MULTIPDF (sin cards, con pad-block)
# -----------------------------
section_title("1. Cargar uno o varios documentos PDF")
pad_start()
uploaded_files = st.file_uploader(
    "Selecciona uno o más archivos PDF",
    type="pdf",
    accept_multiple_files=True,
    key="multi_pdf_upload",
    help="Arrastra y suelta tus PDFs o haz clic para seleccionarlos.",
)
pad_end()

if uploaded_files:
    progress = st.progress(0, text="Procesando documentos...")
    total = len(uploaded_files)
    for idx, archivo in enumerate(uploaded_files, start=1):
        nombre = archivo.name
        if nombre not in st.session_state.multi_resumenes:
            st.info(f"Procesando documento: **{nombre}**")
            docs = extract_text_from_pdf_bytes(archivo.getvalue(), nombre)
            if docs:
                resumen = resumen_documento(docs, llm, RESUMEN_PROMPT)
            else:
                resumen = "Documento vacío o no legible."
            st.session_state.multi_resumenes[nombre] = resumen
        progress.progress(int(idx / total * 100), text=f"Procesado {idx} de {total}")

    section_title("2. Resúmenes Generados")
    for nombre, resumen in st.session_state.multi_resumenes.items():
        pad_start()
        with st.expander(f"Resumen de {nombre}", expanded=False):
            st.markdown(resumen)
        pad_end()

    st.divider()
    if st.button("Limpiar todos los resúmenes"):
        st.session_state.multi_resumenes = {}
        st.success("Se limpiaron los resúmenes generados.")
else:
    pad_start()
    st.info("Por favor, sube uno o más archivos PDF para analizarlos y obtener sus resúmenes.")
    pad_end()

# -----------------------------
# FOOTER
# -----------------------------
footer_corp()
