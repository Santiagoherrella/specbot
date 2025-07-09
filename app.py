# app.py
#streamlit run app.py
import streamlit as st
st.set_page_config(page_title="Asistente de Normativas (FAISS)", layout="centered")

import time
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
# Importar las funciones de nuestro módulo de lógica
from core_logic import (get_llm, 
    get_embeddings_model, 
    load_rag_chain, 
    get_image_decision   
)
# --- Configuración de la Página Streamlit ---
# --- Funciones Cacheadas para Carga de Componentes ---
# Usamos st.cache_resource para asegurar que estos modelos y cadenas
# se carguen solo una vez por sesión de usuario.

@st.cache_resource
def cached_get_llm():
    return get_llm()

@st.cache_resource
def cached_get_embeddings_model():
    return get_embeddings_model()

@st.cache_resource
def cached_load_rag_chain(_llm, _embeddings):
    return load_rag_chain(_llm, _embeddings)

# --- Inicialización de la Aplicación ---
st.title("🤖 Asistente Técnico Avanzado (RAG con LLM-Retriever)")
st.caption("Consulta información sobre la base de conocimiento pre-procesada.")
# Cargar los componentes principales usando las funciones cacheadas
# --- MODO DEPURACIÓN (Checkbox en la barra lateral) ---
with st.sidebar:
    st.header("Opciones")
    debug_mode = st.checkbox("Activar Modo Depuración", value=False)
    st.caption("Activa esta opción para ver los datos internos del proceso RAG en la interfaz.")
try:
    llm_instance = cached_get_llm()
    embeddings_instance = cached_get_embeddings_model()
    conversation_chain_template = cached_load_rag_chain(llm_instance, embeddings_instance)
    
    # Inicializar estado de sesión si es la primera vez
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "¿En qué puedo ayudarte hoy sobre las normativas?"}]
    if "memory" not in st.session_state:
        st.session_state.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key='answer'
        )
except Exception as e:
    st.error(f"Error fatal durante la inicialización de la aplicación: {e}")
    st.stop() # Detener la app si los componentes principales no pueden cargar

# --- Interfaz de Chat ---

# Mostrar el historial de chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Si el mensaje del asistente tiene una imagen asociada, mostrarla
        if message["role"] == "assistant" and "image" in message and message["image"]:
            st.image(message["image"])

# Recibir la entrada del usuario
prompt_usuario = st.chat_input("Escribe tu pregunta aquí...")

if prompt_usuario:
    # Añadir y mostrar el mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt_usuario})
    with st.chat_message("user"):
        st.markdown(prompt_usuario)

    # Procesar la respuesta del asistente
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Pensando y buscando en los documentos...")

        try:
            # Crear una instancia de la cadena para este turno, con la memoria actual
            # Esto asegura que el historial de chat se use correctamente
            current_rag_chain = ConversationalRetrievalChain(
                retriever=conversation_chain_template.retriever,
                combine_docs_chain=conversation_chain_template.combine_docs_chain,
                question_generator=conversation_chain_template.question_generator,
                memory=st.session_state.memory,
                return_source_documents=True
            )

            # 1. Invocar la cadena RAG para obtener la respuesta y los documentos fuente
            result = current_rag_chain.invoke({"question": prompt_usuario})
            respuesta_texto = result.get("answer", "No se pudo generar una respuesta.")
            documentos_fuente = result.get("source_documents", [])
            # --- INICIO DEL BLOQUE DE DEPURACIÓN ---
            if debug_mode:
                with st.expander("🔍 MODO DEPURACIÓN: Ver Datos Internos", expanded=True):
                    st.subheader("Paso 1: Documentos Recuperados por el Retriever")
                    st.write("Estos son los chunks que el `MultiQueryRetriever` consideró más relevantes para tu pregunta:")
                    if documentos_fuente:
                        for i, doc in enumerate(documentos_fuente):
                            st.markdown(f"**Documento {i+1}**")
                            st.json(doc.metadata) # Mostrar metadatos como JSON
                            st.text(doc.page_content)
                    else:
                        st.warning("El retriever no devolvió ningún documento.")
            # --- FIN DEL BLOQUE DE DEPURACIÓN ---
            # ##
            ## 2. Invocar la lógica de decisión de imagen
            #ruta_imagen_para_mostrar, decision_str_debug = get_image_decision(
            #    question=prompt_usuario,
            #    source_documents=documentos_fuente,
            #    llm=llm_instance,
            #    return_debug_info=True # Modificaremos la función para que devuelva esto
            #)
            ## --- INICIO DEL BLOQUE DE DEPURACIÓN ---
            #if debug_mode:
            #   with st.expander("🔍 MODO DEPURACIÓN: Ver Datos Internos", expanded=True):
            #        st.subheader("Paso 2: Decisión de Mostrar Imagen")
            #        st.write("Esta es la respuesta cruda del LLM al pedirle que decida si se necesita una imagen:")
            #        st.text(decision_str_debug)
            #        st.write("Ruta de imagen encontrada (si aplica):", ruta_imagen_para_mostrar or "Ninguna")
            # --- FIN DEL BLOQUE DE DEPURACIÓN ---
            
            # 3. Renderizar la respuesta
            message_placeholder.markdown(respuesta_texto)
           # if ruta_imagen_para_mostrar:
           #   st.image(ruta_imagen_para_mostrar)
            
            # 4. Actualizar el historial de sesión con la respuesta completa
            st.session_state.messages.append({
                "role": "assistant",
                "content": respuesta_texto
                #"image": ruta_imagen_para_mostrar # Guardar la ruta de la imagen en el historial
            })

            # (Opcional) Mostrar las fuentes utilizadas
            if documentos_fuente:
                with st.expander("Ver fuentes utilizadas"):
                    for i, doc in enumerate(documentos_fuente):
                        st.markdown(f"**Fuente {i+1}** (Tipo: {doc.metadata.get('content_type', 'N/A')}, Pág: {doc.metadata.get('page', 'N/A')})")
                        st.caption(f"Contenido: {doc.page_content[:200]}...")

        except Exception as e:
            error_msg = f"Ocurrió un error al procesar tu pregunta: {e}"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg, "image": None})