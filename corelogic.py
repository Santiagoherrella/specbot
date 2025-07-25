import os
from langchain_google_genai import ChatGoogleGenerativeAI
MODEL_NAME_LLM = "models/gemini-2.0-flash"

def get_llm(key):
    """Carga y devuelve el modelo LLM de OpenAI."""
    try:llm = ChatGoogleGenerativeAI(model=MODEL_NAME_LLM, 
                                         temperature=0.3,
                                         google_api_key=key)
        return llm
    except Exception as e:
        print(f"Error al inicializar LLM de OpenAI: {e}")
    
