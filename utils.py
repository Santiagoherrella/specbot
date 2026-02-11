"""utils.py - Extracción de texto de PDFs con soporte OCR automático para documentos escaneados"""

import tempfile
import os
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain.docstore.document import Document

# Importaciones para OCR
try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def extract_text_from_pdf_bytes(uploaded_file_content_bytes, filename):
    """
    Extrae el texto de cada PDF usando PyPDFLoader.
    Si el PDF es escaneado (imagen plana sin texto), aplica OCR automáticamente.
    
    Args:
        uploaded_file_content_bytes: Contenido binario del archivo PDF
        filename: Nombre del archivo PDF
        
    Returns:
        Lista de objetos Document con el texto extraído
    """
    try:
        # Guardar temporalmente el PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file_content_bytes)
            tmp_file_path = tmp_file.name
        
        # Intentar extracción normal con PyPDFLoader
        loader = PyPDFLoader(tmp_file_path)
        langchain_docs = loader.load()
        
        # Calcular cantidad de texto extraído
        total_text = "".join([doc.page_content for doc in langchain_docs])
        total_chars = len(total_text.strip())
        total_pages = len(langchain_docs)
        avg_chars_per_page = total_chars / total_pages if total_pages > 0 else 0
        
        # Detectar si necesita OCR
        # Criterio: menos de 50 caracteres por página = probablemente escaneado
        needs_ocr = avg_chars_per_page < 50
        
        if needs_ocr:
            st.warning(f"⚠️ El PDF '{filename}' parece ser una imagen escaneada (promedio: {avg_chars_per_page:.0f} caracteres/página)")
            
            if OCR_AVAILABLE:
                with st.spinner("🔍 Aplicando OCR... Esto puede tomar unos segundos."):
                    ocr_docs = extract_text_with_ocr(tmp_file_path, filename, total_pages)
                
                # Si el OCR extrajo más texto, usar ese resultado
                ocr_text = "".join([doc.page_content for doc in ocr_docs])
                if len(ocr_text.strip()) > total_chars:
                    langchain_docs = ocr_docs
                    st.success(f"✅ OCR completado exitosamente: {len(ocr_text)} caracteres extraídos")
                else:
                    st.info("ℹ️ Usando extracción normal")
            else:
                st.error("❌ OCR no disponible. Verifica que pytesseract, pdf2image y Pillow estén instalados.")
                st.info("💡 El PDF será procesado con el texto disponible, aunque puede ser limitado.")
        else:
            st.success(f"✅ Texto extraído exitosamente: {total_chars} caracteres")
        
        # Limpiar archivo temporal
        os.remove(tmp_file_path)
        
        # Actualizar metadata
        for doc in langchain_docs:
            doc.metadata["source"] = filename
        
        return langchain_docs
        
    except Exception as e:
        # Si falla la extracción normal, intentar OCR como respaldo
        if OCR_AVAILABLE:
            st.warning(f"⚠️ Error en extracción normal: {e}")
            st.info("🔄 Intentando OCR como respaldo...")
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file_content_bytes)
                    tmp_file_path = tmp_file.name
                
                ocr_docs = extract_text_with_ocr(tmp_file_path, filename)
                os.remove(tmp_file_path)
                
                if ocr_docs:
                    st.success("✅ OCR completado exitosamente")
                    return ocr_docs
            except Exception as ocr_error:
                st.error(f"❌ Error en OCR: {ocr_error}")
        
        st.error(f"Error al extraer texto de '{filename}': {e}")
        return []


def extract_text_with_ocr(pdf_path, filename, total_pages=None):
    """
    Aplica OCR a un PDF escaneado usando Tesseract.
    
    Args:
        pdf_path: Ruta del archivo PDF temporal
        filename: Nombre del archivo original
        total_pages: Número total de páginas (opcional, para mostrar progreso)
    
    Returns:
        Lista de objetos Document con el texto extraído por OCR
    """
    if not OCR_AVAILABLE:
        raise ImportError("OCR no disponible. Instala: pip install pytesseract pdf2image Pillow")
    
    try:
        # Convertir PDF a imágenes (DPI 300 para buena calidad)
        images = convert_from_path(pdf_path, dpi=300)
        
        # Preparar documentos
        ocr_docs = []
        
        # Crear barra de progreso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Aplicar OCR a cada página
        for i, image in enumerate(images):
            # Actualizar progreso
            progress = (i + 1) / len(images)
            progress_bar.progress(progress)
            status_text.text(f"📷 Procesando página {i+1}/{len(images)} con OCR...")
            
            # Extraer texto con Tesseract (español + inglés)
            try:
                text = pytesseract.image_to_string(image, lang='spa+eng')
            except Exception:
                # Si falla con español, intentar solo inglés
                try:
                    text = pytesseract.image_to_string(image, lang='eng')
                except Exception:
                    # Si todo falla, usar sin especificar idioma
                    text = pytesseract.image_to_string(image)
            
            # Crear documento para esta página
            doc = Document(
                page_content=text,
                metadata={
                    "source": filename,
                    "page": i,
                    "extraction_method": "OCR"
                }
            )
            ocr_docs.append(doc)
        
        # Limpiar barra de progreso
        progress_bar.empty()
        status_text.empty()
        
        return ocr_docs
        
    except Exception as e:
        st.error(f"Error durante el proceso de OCR: {e}")
        raise


def resumen_documento(docs, llm_instance, resumen_prompt):
    """
    Genera el resumen de los documentos concatenados usando el LLM.
    
    Args:
        docs: Lista de documentos Document
        llm_instance: Instancia del modelo de lenguaje
        resumen_prompt: Plantilla del prompt para resumen
        
    Returns:
        Texto del resumen generado
    """
    texto = "\n\n".join([doc.page_content for doc in docs])
    texto_corto = texto[:1500000]  # Limita tamaño para el prompt
    prompt = resumen_prompt.format(document_text=texto_corto)
    
    try:
        respuesta = llm_instance.invoke(prompt)
        return respuesta.content.strip() if hasattr(respuesta, 'content') else str(respuesta).strip()
    except Exception as e:
        st.error(f"Error generando resumen: {e}")
        return "No se pudo generar el resumen.""No se pudo generar el resumen."

