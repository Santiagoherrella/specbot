import os
from langchain_openai import ChatOpenAI
MODEL_NAME_LLM = "gpt-4.1-nano-2025-04-14"

def get_llm():
    """Carga y devuelve el modelo LLM de OpenAI."""
    try:
        llm = ChatOpenAI(model_name=MODEL_NAME_LLM, temperature=0.1,
                         api_key=st.secrets["OPENAI_API_KEY"],
                         max_tokens=1500)
        return llm
    except Exception as e:
        print(f"Error al inicializar LLM de OpenAI: {e}")
        raise
