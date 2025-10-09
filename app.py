# app.py
#streamlit run app.py
import time
import base64
import re
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
HERO_PATH = ASSETS / "banner.png"
LOGO = ASSETS / "logo.png"
CORP = "#0f6db4"

st.set_page_config(
    page_title="Analizador MultiPDF IA - Magnetron",
    page_icon=str(LOGO) if LOGO.exists() else "📄",
    layout="wide",
)

# -----------------------------
# UTILIDADES DISEÑO
# -----------------------------
def _b64(path: Path):
    if path.exists():
        return base64.b64encode(path.read_bytes()).decode("utf-8")
    return ""

def limpiar_nombre_archivo(nombre):
    """
    Limpia el nombre del archivo para usarlo en el nombre de descarga.
    Remueve la extensión .pdf y caracteres especiales.
    """
    # Quitar extensión .pdf
    nombre_sin_ext = nombre.replace('.pdf', '').replace('.PDF', '')
    # Reemplazar espacios y caracteres especiales por guiones bajos
    nombre_limpio = re.sub(r'[^a-zA-Z0-9_-]', '_', nombre_sin_ext)
    # Evitar guiones bajos múltiples
    nombre_limpio = re.sub(r'_+', '_', nombre_limpio)
    # Limitar longitud a 50 caracteres
    if len(nombre_limpio) > 50:
        nombre_limpio = nombre_limpio[:50]
    return nombre_limpio

def apply_skin():
    st.markdown(
        f"""
        <style>
        [data-testid="stHeader"] {{
            background-color: {CORP};
            height: 3.5rem;
        }}

        .stMarkdown h3, .stMarkdown h2 {{
            color: white !important;
        }}

        .stButton>button {{
            background-color: {CORP};
            color: white;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            border: none;
            font-weight: 600;
        }}
        .stButton>button:hover {{
            background-color: #0a5690;
        }}

        [data-testid="stFileUploader"] {{
            border: 2px dashed {CORP};
            border-radius: 10px;
            padding: 1rem;
        }}

        .logo-img {{
            max-height: 60px;
            width: auto;
            margin-bottom: 1rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def hero_header(title="Analizador y Resumidor MultiPDF con IA", subtitle=None, show_logo=True):
    if subtitle is None:
        subtitle = f"Hora actual: {time.strftime('%Y-%m-%d %H:%M:%S')}"

    logo_html = ""
    if show_logo and LOGO.exists():
        logo_b64 = _b64(LOGO)
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" class="logo-img" />'

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, {CORP} 0%, #0a5690 100%); padding: 2rem; border-radius: 10px; text-align: center; margin-bottom: 2rem;">
            {logo_html}
            <h1 style="color: white; margin: 0;">📄 {title}</h1>
            <p style="color: rgba(255,255,255,0.9); margin-top: 0.5rem;">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------
# SISTEMA DE LOGIN
# -----------------------------
def login_screen():
    st.markdown(
        f"""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="color: {CORP};">🔐 Iniciar Sesión</h2>
            <p style="color: #666;">Ingresa tu nombre para continuar</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        nombre_usuario = st.text_input(
            "Nombre completo",
            placeholder="Ej: Juan Pérez",
            key="login_nombre"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🚀 Ingresar", use_container_width=True, key="btn_login"):
            if nombre_usuario and nombre_usuario.strip():
                st.session_state.logged_in = True
                st.session_state.usuario = nombre_usuario.strip()
                st.rerun()
            else:
                st.error("⚠️ Por favor ingresa tu nombre")

# -----------------------------
# FUNCIÓN PRINCIPAL
# -----------------------------
def main():
    # Inicializar session_state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "usuario" not in st.session_state:
        st.session_state.usuario = ""
    if "ultimo_resumen" not in st.session_state:
        st.session_state.ultimo_resumen = None
    if "nombre_pdfs" not in st.session_state:
        st.session_state.nombre_pdfs = None
    if "nombre_archivo_limpio" not in st.session_state:
        st.session_state.nombre_archivo_limpio = None

    apply_skin()

    # Si no está logueado
    if not st.session_state.logged_in:
        hero_header(
            title="Analizador MultiPDF con IA",
            subtitle="Sistema de análisis de pliegos técnicos - Magnetron S.A.S.",
            show_logo=True
        )
        login_screen()
        return

    # Usuario logueado
    hero_header(
        title="Analizador MultiPDF con IA",
        subtitle=f"Usuario: {st.session_state.usuario} | {time.strftime('%Y-%m-%d %H:%M:%S')}",
        show_logo=True
    )

    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🚪 Salir", key="btn_logout"):
            st.session_state.logged_in = False
            st.session_state.usuario = ""
            st.session_state.ultimo_resumen = None
            st.session_state.nombre_pdfs = None
            st.session_state.nombre_archivo_limpio = None
            st.rerun()

    st.markdown("---")

    st.info(
        "📋 **Sube uno o varios pliegos en PDF** y genera un **Resumen Ejecutivo** "
        "detallado con información técnica clave y tablas listas para Excel."
    )

    # Subida de archivos
    uploaded_files = st.file_uploader(
        "🗂️ Arrastra o selecciona tus archivos PDF",
        type=["pdf"],
        accept_multiple_files=True,
        help="Puedes subir múltiples PDFs a la vez",
        key="file_uploader"
    )

    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} archivo(s) cargado(s)")

        with st.expander("📄 Ver archivos cargados"):
            for i, file in enumerate(uploaded_files, 1):
                st.write(f"{i}. **{file.name}** ({file.size / 1024:.1f} KB)")

        st.markdown("---")

        # MOSTRAR RESUMEN SI EXISTE (FUERA DEL BOTÓN)
        if st.session_state.ultimo_resumen:
            st.success("✅ ¡Resumen generado exitosamente!")
            st.markdown("## 📊 Resumen Ejecutivo")
            st.info(f"**Archivo(s):** {st.session_state.nombre_pdfs}")

            with st.container():
                st.markdown(st.session_state.ultimo_resumen)

            col_download, col_nuevo = st.columns([3, 1])

            with col_download:
                st.download_button(
                    label="📥 Descargar Resumen (.txt)",
                    data=st.session_state.ultimo_resumen,
                    file_name=f"resumen_{st.session_state.nombre_archivo_limpio}.txt",
                    mime="text/plain",
                    key="btn_download"
                )

            with col_nuevo:
                if st.button("🔄 Nuevo Análisis", key="btn_nuevo"):
                    st.session_state.ultimo_resumen = None
                    st.session_state.nombre_pdfs = None
                    st.session_state.nombre_archivo_limpio = None
                    st.rerun()

            st.markdown("---")

        # BOTÓN PARA PROCESAR PDFs
        if st.button("🔄 Procesar PDFs y Generar Resumen", use_container_width=True, type="primary", key="btn_process"):

            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                status_text.text("⚙️ Inicializando modelo de IA...")
                progress_bar.progress(20)
                llm = get_llm()
                prompt_summary = get_prompt_summary_str()

                status_text.text("📄 Extrayendo texto de los PDFs...")
                progress_bar.progress(40)

                all_docs = []
                for idx, uploaded_file in enumerate(uploaded_files):
                    file_bytes = uploaded_file.read()
                    docs = extract_text_from_pdf_bytes(file_bytes, uploaded_file.name)
                    all_docs.extend(docs)
                    progress_bar.progress(40 + (idx + 1) * (30 // len(uploaded_files)))

                if not all_docs:
                    st.error("❌ No se pudo extraer texto de los PDFs.")
                    return

                status_text.text(f"🤖 Generando resumen de {len(all_docs)} página(s)...")
                progress_bar.progress(70)

                resumen = resumen_documento(all_docs, llm, prompt_summary)

                progress_bar.progress(100)
                status_text.empty()
                progress_bar.empty()

                # GUARDAR EN SESSION_STATE
                st.session_state.ultimo_resumen = resumen
                st.session_state.nombre_pdfs = ", ".join([f.name for f in uploaded_files])

                # Generar nombre limpio para el archivo de descarga
                if len(uploaded_files) == 1:
                    st.session_state.nombre_archivo_limpio = limpiar_nombre_archivo(uploaded_files[0].name)
                else:
                    st.session_state.nombre_archivo_limpio = f"multiple_{len(uploaded_files)}_pdfs"

                st.rerun()  # Recarga para mostrar el resumen

            except Exception as e:
                st.error(f"❌ Error al procesar: {str(e)}")
                import traceback
                with st.expander("🔍 Ver detalles del error"):
                    st.code(traceback.format_exc())
    else:
        st.warning("⬆️ Sube al menos un archivo PDF para comenzar")

    # Footer
    st.markdown("---")
    if LOGO.exists():
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            logo_b64 = _b64(LOGO)
            st.markdown(
                f"""
                <div style="text-align: center;">
                    <img src="data:image/png;base64,{logo_b64}" style="max-width: 80px; opacity: 0.7;" />
                    <p style="color: #888; font-size: 0.9rem; margin-top: 0.5rem;">
                        Magnetron S.A.S. | Analizador v2.0
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.markdown(
            '<p style="text-align: center; color: #888;">Magnetron S.A.S. | Analizador de Pliegos Técnicos v2.0</p>',
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()
