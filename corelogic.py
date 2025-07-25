import os
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
MODEL_NAME_LLM = "gpt-4.1-nano-2025-04-14"
def get_llm(key):
    """Carga y devuelve el modelo LLM de OpenAI."""
    try:
        llm = ChatOpenAI(model_name=MODEL_NAME_LLM, temperature=0.1,
                         api_key=key,
                         max_tokens=1500)
        return llm
    except Exception as e:
        print(f"Error al inicializar LLM de OpenAI: {e}")
        raise
MODEL_NAME_LLMGEM= "models/gemini-2.0-flash"
def get_llmgem(key):
    """Carga y devuelve el modelo LLM de OpenAI."""
    try:
            llm = ChatGoogleGenerativeAImodel=(MODEL_NAME_LLMGEM,
                              temperature=0.3, 
                              api_key=key)
            return llm
    except Exception as e:
        print(f"Error al inicializar LLM de GEMINI: {e}")
        raise
