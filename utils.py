import tempfile
import os
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader

def extract_text_from_pdf_bytes(uploaded_file_content_bytes, filename):
    """
    Extrae el texto de cada PDF usando PyPDFLoader y devuelve una lista de objetos Document.
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file_content_bytes)
            tmp_file_path = tmp_file.name
        loader = PyPDFLoader(tmp_file_path)
        langchain_docs = loader.load()
        os.remove(tmp_file_path)
        for doc in langchain_docs:
            doc.metadata["source"] = filename
        return langchain_docs
    except Exception as e:
        st.error(f"Error al extraer texto de '{filename}': {e}")
        return []

def resumen_documento(docs, llm_instance, resumen_prompt):
    """
    Genera el resumen de los documentos concatenados usando el LLM.
    """
    texto = "\n\n".join([doc.page_content for doc in docs])
    texto_corto = texto[:1500000]  # Limita tamaño para el prompt
    prompt = resumen_prompt.format(document_text=texto_corto)
    try:
        respuesta = llm_instance.invoke(prompt)
        return respuesta.content.strip() if hasattr(respuesta, 'content') else str(respuesta).strip()
    except Exception as e:
        st.error(f"Error generando resumen: {e}")
        return "No se pudo generar el resumen."