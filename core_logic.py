# core_logic.py
import os
import json
import re
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.prompts import PromptTemplate
from prompts import get_custom_rag_prompt

# --- Configuración de Constantes ---
PERSIST_DIRECTORY = "vector_store_faiss_multimodal"
MODEL_NAME_EMBEDDING = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_NAME_LLM = "gpt-4.1-nano-2025-04-14"

# --- Prompt para el Analista de Contexto (Decisión de Imagen) ---
image_decision_prompt_template = """
Eres un analista de contexto. Tu tarea es analizar una pregunta de usuario y el texto recuperado de documentos técnicos.
El texto recuperado puede contener descripciones de figuras (ej. "Figure 1", "Fig. 2-A").
Basado en la pregunta y el texto, decide si mostrar una imagen específica mejoraría significativamente la respuesta.

Si el texto recuperado menciona una figura que es directamente relevante para la pregunta, responde ÚNICAMENTE con un objeto JSON que contenga el identificador de esa figura.
Ejemplo de respuesta: {"image_needed": true, "figure_id": "Figure 1"}

Si múltiples figuras son relevantes, devuelve la primera que encuentres.
Si no se menciona ninguna figura relevante o si el texto no es suficiente para justificar una imagen, responde ÚNICAMENTE con: {"image_needed": false}

Pregunta del Usuario: "{question}"

Texto Recuperado:
---
{context}
---

JSON de Decisión:
"""
IMAGE_DECISION_PROMPT = PromptTemplate(
    template=image_decision_prompt_template, input_variables=["question", "context"]
)

# --- Funciones de Carga de Modelos y Componentes ---

def get_embeddings_model():
    """Carga y devuelve el modelo de embedding."""
    print("Inicializando modelo de embedding...")
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': True}
    embeddings_model = HuggingFaceEmbeddings(
        model_name=MODEL_NAME_EMBEDDING,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )
    return embeddings_model

def get_llm():
    """Carga y devuelve el modelo LLM de OpenAI."""
    if 'OPENAI_API_KEY' not in os.environ:
        raise ValueError("La variable de entorno OPENAI_API_KEY no está configurada.")
    print(f"Inicializando LLM de OpenAI: {MODEL_NAME_LLM}...")
    try:
        llm = ChatOpenAI(model_name=MODEL_NAME_LLM, temperature=0.1, max_tokens=1500)
        return llm
    except Exception as e:
        print(f"Error al inicializar LLM de OpenAI: {e}")
        raise

def load_rag_chain(llm, embeddings_model):
    """
    Carga el Vector Store FAISS, crea un MultiQueryRetriever y una cadena conversacional.
    """
    if not os.path.exists(PERSIST_DIRECTORY):
        raise FileNotFoundError(f"El directorio del Vector Store '{PERSIST_DIRECTORY}' no existe. Ejecuta primero el script de ingesta.")

    print(f"Cargando índice FAISS desde: {PERSIST_DIRECTORY}...")
    try:
        vectorstore = FAISS.load_local(
            folder_path=PERSIST_DIRECTORY,
            embeddings=embeddings_model,
            allow_dangerous_deserialization=True
        )
        print("¡Índice FAISS cargado!")
    except Exception as e:
        print(f"Error al cargar el índice FAISS: {e}")
        raise

    # Crear el retriever base
    base_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    # Crear el MultiQueryRetriever (Retriever dirigido por LLM)
    print("Creando MultiQueryRetriever...")
    retriever_mq = MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=llm
    )

    # Crear la cadena conversacional (sin memoria, se añadirá en la UI)
    print("Creando plantilla de cadena conversacional...")
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever_mq, # Usar el retriever MultiQuery
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": get_custom_rag_prompt()}
    )
    print("¡Componentes RAG listos!")
    return conversation_chain

# --- FUNCIÓN CORREGIDA Y MÁS ROBUSTA (VERSIÓN 2) ---
def get_image_decision(question, source_documents, llm, return_debug_info=False):
    """
    Usa un LLM para decidir si se necesita una imagen y cuál.
    Devuelve la ruta a la imagen si es necesaria, de lo contrario None.
    Si return_debug_info es True, devuelve una tupla (image_path, raw_llm_response).
    """
    decision_str = "" # Inicializar por si falla la llamada al LLM
    if not source_documents:
        print("DEBUG (get_image_decision): No se proporcionaron documentos fuente.")
        return None

    context_text = "\n\n---\n\n".join([doc.page_content for doc in source_documents])
    decision_prompt_formatted = IMAGE_DECISION_PROMPT.format(
        question=question,
        context=context_text
    )

    try:
        response = llm.invoke(decision_prompt_formatted)
        decision_str = response.content.strip() if hasattr(response, 'content') else str(response).strip()
        
        print(f"DEBUG (get_image_decision): Respuesta cruda del LLM -> '{decision_str}'")

        json_match = re.search(r'\{.*\}', decision_str, re.DOTALL)
        if not json_match:
            print("DEBUG (get_image_decision): No se encontró un objeto JSON en la respuesta con regex.")
            return None

        json_string = json_match.group(0)
        print(f"DEBUG (get_image_decision): String JSON extraído -> '{json_string}'")

        try:
            decision_json = json.loads(json_string)
        except json.JSONDecodeError:
            print(f"DEBUG (get_image_decision): Error de decodificación JSON. El string extraído no es un JSON válido.")
            return None

        if decision_json.get("image_needed") and decision_json.get("figure_id"):
            figure_to_find = decision_json.get("figure_id")
            print(f"DEBUG (get_image_decision): Decisión del LLM: Se necesita imagen para '{figure_to_find}'.")
            
            for doc in source_documents:
                if doc.metadata.get("content_type") == "image_description" and doc.metadata.get("figure_id") == figure_to_find:
                    image_path = doc.metadata.get("image_path")
                    if image_path and os.path.exists(image_path):
                        print(f"DEBUG (get_image_decision): Encontrada ruta de imagen válida: {image_path}")
                        if return_debug_info:
                            return image_path, decision_str
                    else:
                        print(f"DEBUG (get_image_decision): Advertencia - La ruta de imagen '{image_path}' no existe en el disco.")
            print(f"DEBUG (get_image_decision): Advertencia - No se encontró la ruta para la figura '{figure_to_find}' en los metadatos recuperados.")
        else:
            print("DEBUG (get_image_decision): Decisión del LLM: No se necesita imagen o falta figure_id en el JSON.")
            
    except Exception as e:
        # Captura cualquier otro error inesperado durante la invocación del LLM o el procesamiento
        print(f"ERROR (get_image_decision): Ocurrió un error inesperado de tipo {type(e).__name__}: {e}")
    try:
        # ... (el resto del código de la función se mantiene igual hasta el final) ...

        # AL FINAL DE LA FUNCIÓN, justo antes del 'return None' final:
        if return_debug_info:
            return None, decision_str
        else:
            return None

    except Exception as e:
        print(f"ERROR (get_image_decision): Ocurrió un error inesperado de tipo {type(e).__name__}: {e}")
        if return_debug_info:
            return None, f"Error: {e}"
        else:
            return None
    return None
