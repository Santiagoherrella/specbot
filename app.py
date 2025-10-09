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

def apply_skin():
    hero_bg = _b64(HERO_PATH)
    st.markdown(
        f"""
        <style>
        /* Header fijo */
        [data-testid="stHeader"] {{
            background-color: {CORP};
            height: 3.5rem;
        }}

        /* Subheaders en blanco */
        .stMarkdown h3, .stMarkdown h2 {{
            color: white !important;
        }}

        /* Botones corporativos */
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

        /* File uploader */
        [data-testid="stFileUploader"] {{
            border: 2px dashed {CORP};
            border-radius: 10px;
            padding: 1rem;
        }}

        /* Logo styling */
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

    # Si existe el logo, mostrarlo en el header
    logo_html = ""
    if show_logo and LOGO.exists():
        logo_b64 = _b64(LOGO)
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" class="logo-img" />'

    st.markdown(
        f"""
        <div class="hero-container" style="
            background: linear-gradient(135deg, {CORP} 0%, #0a5690 100%);
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 2rem;
        ">
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
    # Logo en la pantalla de login
    if LOGO.exists():
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            logo_b64 = _b64(LOGO)
            st.markdown(
                f"""
                <div style="text-align: center; margin-bottom: 2rem;">
                    <img src="data:image/png;base64,{logo_b64}" style="max-width: 200px; width: 100%;" />
                </div>
                """,
                unsafe_allow_html=True
            )

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

    # Aplicar estilos
    apply_skin()

    # Si no está logueado, mostrar login
    if not st.session_state.logged_in:
        hero_header(
            title="Analizador MultiPDF con IA",
            subtitle="Sistema de análisis de pliegos técnicos - Magnetron S.A.S.",
            show_logo=True  # No mostrar logo aquí porque lo mostramos abajo más grande
        )
        login_screen()
        return

    # --- USUARIO LOGUEADO ---
    hero_header(
        title="Analizador MultiPDF con IA",
        subtitle=f"Usuario: {st.session_state.usuario} | {time.strftime('%Y-%m-%d %H:%M:%S')}",
        show_logo=True
    )

    # Botón de cerrar sesión en la esquina
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🚪 Salir", key="btn_logout"):
            st.session_state.logged_in = False
            st.session_state.usuario = ""
            st.rerun()

    st.markdown("---")

    # Descripción
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

        # Mostrar lista de archivos
        with st.expander("📄 Ver archivos cargados"):
            for i, file in enumerate(uploaded_files, 1):
                st.write(f"{i}. **{file.name}** ({file.size / 1024:.1f} KB)")

        st.markdown("---")
        # Mostrar resumen si existe en session_state
    if "ultimo_resumen" in st.session_state and st.session_state.ultimo_resumen:
        st.success("✅ ¡Resumen generado exitosamente!")
        st.markdown("---")
        st.markdown("## 📊 Resumen Ejecutivo")
    
    with st.container():
        st.markdown(st.session_state.ultimo_resumen)
    
    # Botón de descarga (ahora desde session_state)
    st.download_button(
        label="📥 Descargar Resumen (.txt)",
        data=st.session_state.ultimo_resumen,
        file_name=f"resumen_{st.session_state.nombre_pdfs.replace(', ', '_')}_{time.strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
        key="btn_download"
    )

        # BOTÓN MANUAL PARA PROCESAR
    if st.button("🔄 Procesar PDFs y Generar Resumen", use_container_width=True, type="primary", key="btn_process"):

            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # Paso 1: Cargar LLM
                status_text.text("⚙️ Inicializando modelo de IA...")
                progress_bar.progress(20)
                llm = get_llm()
                prompt_summary = get_prompt_summary_str()

                # Paso 2: Procesar PDFs
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

                # Paso 3: Generar resumen
                status_text.text(f"🤖 Generando resumen de {len(all_docs)} página(s)...")
                progress_bar.progress(70)

                resumen = resumen_documento(all_docs, llm, prompt_summary)

                st.session_state.ultimo_resumen = resumen  # Guardamos el resumen
                st.session_state.ultimo_pdf = ", ".join([f.name for f in uploaded_files])  # Nombre(s) del PDF

                progress_bar.progress(100)
                status_text.empty()
                progress_bar.empty()

                # Mostrar resultado
                st.success("✅ ¡Resumen generado exitosamente!")
                st.rerun()  # ← Recarga para mostrar desde session_state
                st.markdown("---")
                st.markdown("## 📊 Resumen Ejecutivo")

                # Contenedor con el resumen
                with st.container():
                    st.markdown(resumen)

                # Botón de descarga
                st.download_button(
                    label="📥 Descargar Resumen (.txt)",
                    data=resumen,
                    file_name=f"resumen_ejecutivo_{time.strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    key="btn_download"
                )

            except Exception as e:
                st.error(f"❌ Error al procesar: {str(e)}")
                import traceback
                with st.expander("🔍 Ver detalles del error"):
                    st.code(traceback.format_exc())
    else:
        st.warning("⬆️ Sube al menos un archivo PDF para comenzar")

    # Footer con logo pequeño
    st.markdown("---")
    if LOGO.exists():
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            logo_b64 = _b64(LOGO)
            st.markdown(
                f'''
                <div style="text-align: center;">
                    <img src="data:image/png;base64,{logo_b64}" style="max-width: 80px; opacity: 0.7;" />
                    <p style="color: #888; font-size: 0.9rem; margin-top: 0.5rem;">
                        Magnetron S.A.S. | Analizador v2.0
                    </p>
                </div>
                ''',
                unsafe_allow_html=True
            )
    else:
        st.markdown(
            '<p style="text-align: center; color: #888;">Magnetron S.A.S. | Analizador de Pliegos Técnicos v2.0</p>',
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()




