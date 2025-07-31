import streamlit as st
import time

from corelogic import get_llm
from utils import extract_text_from_pdf_bytes, resumen_documento
from promots import get_prompt_summary_str 

# --- Configuración base de la página ---
st.set_page_config(page_title="Analizador MultiPDF IA", layout="wide")

# --- Cacheamos el LLM para evitar inicialización múltiple ---
@st.cache_resource
def cached_llm():
    return get_llm()

# --- Inicializamos prompts y modelo ---
RESUMEN_PROMPT = get_prompt_summary_str()
llm = cached_llm()

# --- Inicialización del estado para múltiples documentos ---
if "multi_resumenes" not in st.session_state:
    st.session_state.multi_resumenes = {}

# --- Interfaz de usuario ---
st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR9JyBfUQZXzv2P5zfX2DEMBqCSrLGTVIxNCA&s", width=80)
st.title("📄 Analizador y Resumidor MultiPDF con IA")
st.caption(f"Hora actual: {time.strftime('%Y-%m-%d %H:%M:%S')}")

st.header("1. Cargar uno o varios documentos PDF")
uploaded_files = st.file_uploader(
    "Selecciona uno o más archivos PDF",
    type="pdf",
    accept_multiple_files=True,
    key="multi_pdf_upload"
)

if uploaded_files:
    for archivo in uploaded_files:
        nombre = archivo.name
        if nombre not in st.session_state.multi_resumenes:
            st.info(f"Procesando documento: {nombre}")
            # Extrae textos de cada archivo PDF usando utilidades
            docs = extract_text_from_pdf_bytes(archivo.getvalue(), nombre)
            if docs:
                # Genera resumen usando función utilitaria
                resumen = resumen_documento(docs, llm, RESUMEN_PROMPT)
            else:
                resumen = "Documento vacío o no legible."
            # Guarda resumen en estado para mostrar posteriormente
            st.session_state.multi_resumenes[nombre] = resumen

    # Mostrar los resúmenes generados
    st.header("2. Resúmenes Generados")
    for nombre, resumen in st.session_state.multi_resumenes.items():
        with st.expander(f"Resumen de {nombre}", expanded=False):
            st.markdown(resumen)

    # Botón para limpiar todos los resúmenes
    if st.button("Limpiar todos los resúmenes"):
        st.session_state.multi_resumenes = {}
else:
    st.info("Por favor, sube uno o más archivos PDF para analizarlos y obtener sus resúmenes.")