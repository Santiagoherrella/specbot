"""
corelogic.py - Gestión de selección e inicialización de modelos de lenguaje.
Permite escoger proveedor y modelo vía config.json y variables de entorno/Streamlit secrets.
Extensible a más LLMs.
"""

import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
import streamlit as st

# Cargar variables de entorno (.env) si ejecutas en local (no es obligatorio en Streamlit Cloud)
load_dotenv()

# Leer configuración desde config.json
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

LLM_PROVIDER = config.get("llm_provider").lower()
MODEL_NAME_LLM = config.get("llm_model")
TEMPERATURE = config.get("temperature")

def get_llm():
    """
    Inicializa y devuelve la instancia del modelo LLM según proveedor definido en config.json.
    Usa las claves desde st.secrets (Streamlit Cloud compatible).
    """
    if LLM_PROVIDER == "openai":
        api_key = st.secrets["OPENAI_API_KEY"]
        return ChatOpenAI(
            model=MODEL_NAME_LLM,
            temperature=TEMPERATURE,
            api_key=api_key
        )
    elif LLM_PROVIDER == "gemini":
        api_key = st.secrets["GOOGLE_API_KEY"]
        return ChatGoogleGenerativeAI(
            model=MODEL_NAME_LLM,
            temperature=TEMPERATURE,
            google_api_key=api_key
        )
    else:
        raise ValueError(f"Proveedor de LLM no soportado: {LLM_PROVIDER}")

