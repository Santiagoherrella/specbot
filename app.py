#streamlit run app.py
#venv\Scripts\activate
# pip install -r requirements.txt 
# deactivate
# streamlit_adhoc_doc_analyzer.py
import streamlit as st
import time
import os
import tempfile
import tabula

# Importaciones de LangChain y OpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain_core.documents import Document
from promots import get_prompt_RAG_str
from promots import get_prompt_summary_str 
from dotenv import load_dotenv
from corelogic import (get_llm)
load_dotenv()

# --- Configuración de la Página Streamlit (MOVIDO AL PRINCIPIO) ---
st.set_page_config(page_title="Analizador de Documentos Ad-Hoc", layout="wide")


# --- Configuración General ---

# --- Prompt para Resumen Ejecutivo ---

EXECUTIVE_SUMMARY_PROMPT = get_prompt_summary_str () 
# --- Prompt para RAG sobre el Documento Cargado ---

CUSTOM_RAG_DOC_PROMPT = get_prompt_RAG_str()

# --- Funciones Cacheadas ---
key = st.secrets["OPENAI_API_KEY"]
@st.cache_resource
def cached_get_llm()key:
    return get_llm()


def extract_text_from_pdf_bytes(uploaded_file_content_bytes, filename="documento_cargado.pdf"):
    """Extrae texto de un archivo PDF cargado (contenido en bytes) y devuelve Documents de Langchain."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file_content_bytes)
            tmp_file_path = tmp_file.name
        
        loader = PyPDFLoader(tmp_file_path)
        # .load() devuelve una lista de Document, uno por página.
        langchain_docs = loader.load() 
        os.remove(tmp_file_path)

        if not langchain_docs:
            st.warning("No se pudo extraer contenido del PDF o el PDF está vacío.")
            return None
        
        # Asignar el nombre de archivo original a los metadatos de cada Documento de página
        for doc in langchain_docs:
            doc.metadata["source"] = filename
            doc.metadata["filename"] = filename
            # 'page' ya es añadido por PyPDFLoader

        return langchain_docs
    except Exception as e:
        st.error(f"Error al extraer texto del PDF: {e}")
        return None
    

# --- Inicialización de Modelos ---
llm_instance = get_llm()

# --- Inicialización del Estado de Sesión para el Documento Ad-Hoc ---
if "adhoc_filename" not in st.session_state:
    st.session_state.adhoc_filename = None
if "adhoc_summary" not in st.session_state:
    st.session_state.adhoc_summary = None
if "adhoc_retriever" not in st.session_state: # Cambiado de pliego_retriever
    st.session_state.adhoc_retriever = None
if "adhoc_chain" not in st.session_state: # Cambiado de pliego_chain
    st.session_state.adhoc_chain = None
if "adhoc_messages" not in st.session_state: # Cambiado de pliego_messages
    st.session_state.adhoc_messages = [
        {"role": "assistant", "content": "Carga un documento PDF para generar un resumen y luego hacer preguntas específicas sobre él."}
    ]

# --- Interfaz Principal Streamlit ---

st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR9JyBfUQZXzv2P5zfX2DEMBqCSrLGTVIxNCA&s", width=80) # Logo de ejemplo
st.title("📄 Analizador y Chat de Documento Ad-Hoc")
st.caption(f"Hora actual en Pereira: {time.strftime('%Y-%m-%d %H:%M:%S %Z')}")


# --- Sección de Carga y Análisis de Documento ---
st.header("1. Cargar y Analizar Documento")
uploaded_doc_file = st.file_uploader("Selecciona un archivo PDF", type="pdf", key="doc_uploader")

# Botón para limpiar el análisis actual y permitir nueva carga
if st.session_state.adhoc_filename:
    if st.button(f"Limpiar análisis de '{st.session_state.adhoc_filename}' y cargar nuevo", key="clear_adhoc_button"):
        st.session_state.adhoc_filename = None
        st.session_state.adhoc_summary = None
        st.session_state.adhoc_retriever = None
        st.session_state.adhoc_chain = None
        st.session_state.adhoc_messages = [{"role": "assistant", "content": "Carga un nuevo documento PDF para análisis."}]
        st.rerun() # Forzar rerun para actualizar la UI

if uploaded_doc_file is not None:
    # Mostrar botón de análisis solo si no se ha procesado este archivo específico o si se limpió
    if uploaded_doc_file.name != st.session_state.get("adhoc_filename_processed_for_chat"):
        if st.button(f"Analizar '{uploaded_doc_file.name}'", key="analyze_doc_button"):
            # Limpiar estado anterior si se analiza uno nuevo
            st.session_state.adhoc_filename = uploaded_doc_file.name
            st.session_state.adhoc_summary = None
            st.session_state.adhoc_retriever = None
            st.session_state.adhoc_chain = None
            st.session_state.adhoc_messages = [{"role": "assistant", "content": f"Analizando '{st.session_state.adhoc_filename}'..."}]
            

            with st.spinner(f"Procesando '{uploaded_doc_file.name}'... Esto puede tardar."):
                doc_content_bytes = uploaded_doc_file.getvalue()
                # extract_text_from_pdf_bytes ahora devuelve una lista de Langchain Documents
                langchain_docs_from_pdf = extract_text_from_pdf_bytes(doc_content_bytes, uploaded_doc_file.name)

                if langchain_docs_from_pdf:
                    # Unir el contenido de todas las páginas para el resumen
                    full_text_for_summary = "\n\n".join([doc.page_content for doc in langchain_docs_from_pdf])
                    st.info(f"Texto extraído ({len(full_text_for_summary)} caracteres). Generando resumen...")
                    
                    try:
                        max_chars_for_summary = 15000
                        texto_para_resumen = full_text_for_summary[:max_chars_for_summary]
                        summary_prompt_formatted = EXECUTIVE_SUMMARY_PROMPT.format(document_text=texto_para_resumen)
                        respuesta_resumen = llm_instance.invoke(summary_prompt_formatted)
                        resumen_ejecutivo = respuesta_resumen.content.strip() if hasattr(respuesta_resumen, 'content') else str(respuesta_resumen).strip()
                        st.session_state.adhoc_summary = resumen_ejecutivo
                    except Exception as e:
                        st.error(f"Error al generar el resumen: {e}")
                        st.session_state.adhoc_summary = "No se pudo generar el resumen."
                    
                            
# Mostrar resumen si está disponible (después del análisis)
if st.session_state.adhoc_filename and st.session_state.adhoc_summary:
    st.subheader(f"Resumen de '{st.session_state.adhoc_filename}':")
    st.markdown(st.session_state.adhoc_summary)

elif uploaded_doc_file and not st.session_state.get("adhoc_filename_processed_for_chat"):
    st.info(f"Haz clic en el botón 'Analizar \"{uploaded_doc_file.name}\"' para procesar y chatear sobre este documento.")
elif not uploaded_doc_file:
    st.info("Carga un documento PDF en la sección superior para generar un resumen y habilitar el chat sobre él.")
