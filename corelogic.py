"""corelogic.py - Gestión de selección e inicialización de modelos de lenguaje.
Permite escoger proveedor y modelo vía config.json y variables de entorno.
Extensible a más LLMs.
"""
import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
# Cargar variables de entorno (.env)
load_dotenv()

# Leer configuración desde config.json
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

LLM_PROVIDER = config.get("llm_provider").lower()
MODEL_NAME_LLM = config.get("llm_model")
TEMPERATURE = config.get("temperature")

def get_llm():
    
    if LLM_PROVIDER == "openai":
        """Carga y devuelve el modelo LLM de OpenAI."""
        if 'OPENAI_API_KEY' not in os.environ:
            raise ValueError("La variable de entorno OPENAI_API_KEY no está configurada.")
        print(f"Inicializando LLM de OpenAI: {MODEL_NAME_LLM}...")
        try:
            llm = ChatOpenAI(
                            model=MODEL_NAME_LLM,
                            api_key=os.getenv("OPENAI_API_KEY")
                            )
            return llm
        except Exception as e:
            print(f"Error al inicializar LLM de OpenAI: {e}")
            raise
    elif LLM_PROVIDER == "gemini":
        """Carga y devuelve el modelo LLM de Gemini."""
        if 'GOOGLE_API_KEY' not in os.environ:
            raise ValueError("La variable de entorno GOOGLE_API_KEY no está configurada.")
        print(f"Inicializando LLM de Gemini: {MODEL_NAME_LLM}...")
        try:
            llm = ChatGoogleGenerativeAI(model=MODEL_NAME_LLM, 
                                         temperature=TEMPERATURE,
                                         google_api_key=os.getenv("GOOGLE_API_KEY"))
            return llm
        except Exception as e:
            print(f"Error al inicializar LLM de Gemini: {e}")
            raise
    else:
        raise ValueError(f"Proveedor de LLM no soportado: {LLM_PROVIDER}")

