# build_vector_store_multimodal.py
import os
import shutil
import time
import fitz  # PyMuPDF
import re
import tabula # Para extracción de tablas
import pandas as pd
from langchain.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# --- Configuración ---
SOURCE_DIRECTORY = "documentos_normativas"
PERSIST_DIRECTORY = "vector_store_faiss_multimodal" # Nuevo directorio para la DB multimodal
IMAGE_OUTPUT_DIRECTORY = os.path.join(PERSIST_DIRECTORY, "imagenes_extraidas") # Guardar imágenes junto a la DB

MODEL_NAME_EMBEDDING = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

# --- Funciones de Extracción y Procesamiento ---

def extract_images_from_pdf(pdf_path, output_folder="imagenes_extraidas"):
    """
    Extrae imágenes de un PDF y las guarda, devolviendo una lista con sus metadatos.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    images_metadata = []
    doc = fitz.open(pdf_path)
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        image_list = page.get_images(full=True)
        
        for img_index, img_info in enumerate(image_list, start=1):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            image_filename = f"{os.path.basename(pdf_path).replace('.pdf', '')}_page{page_num + 1}_img{img_index}.{image_ext}"
            image_path = os.path.join(output_folder, image_filename)
            
            with open(image_path, "wb") as f_img:
                f_img.write(image_bytes)
            
            images_metadata.append({
                "image_path": image_path,
                "page": page_num + 1,
                "source_doc": os.path.basename(pdf_path)
            })
            
    doc.close()
    return images_metadata

def find_caption_for_image(full_text, page_num, source_doc):
    """
    Intenta encontrar un pie de foto para una imagen.
    ¡ESTA ES UNA LÓGICA SIMPLIFICADA Y NECESITA ADAPTACIÓN!
    """
    pattern = re.compile(r"(Figure|Fig\.|Table)\s*([\d\-\.]+)\s*([—–-].*?)(?=\n|Figure|Fig\.|Table)", re.IGNORECASE)
    matches = pattern.findall(full_text)
    
    if matches:
        caption_type, fig_num, description = matches[0]
        full_caption = f"{caption_type.strip()} {fig_num.strip()} {description.strip()}"
        return full_caption, f"{caption_type.strip()} {fig_num.strip()}"
        
    return f"Imagen extraída de {source_doc}, página {page_num}", "Unknown Figure"

def extract_tables_as_docs(pdf_path):
    """
    Extrae tablas de un PDF usando Tabula y las devuelve como una lista de Documentos de LangChain.
    """
    if tabula is None:
        return [] # Devolver lista vacía si tabula no está instalado

    table_docs = []
    print(f"  Intentando extraer tablas de {os.path.basename(pdf_path)} con Tabula...")
    try:
        # read_pdf devuelve una lista de DataFrames de Pandas.
        # stream=True es bueno para tablas sin líneas claras. lattice=True para tablas con bordes.
        dfs = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True, pandas_options={'dtype': str})
        
        for idx, df in enumerate(dfs):
            if df.empty:
                continue
            df = df.fillna("")
            texto_tabla = df.to_csv(sep="\t", index=False, header=True)
            doc = Document(
                page_content=texto_tabla,
                metadata={
                    "source": pdf_path,
                    "filename": os.path.basename(pdf_path),
                    "tipo_contenido": "tabla",
                    "tabla_id": idx + 1,
                    "titulo_tabla": f"Tabla {idx + 1}"
                }
            )
            table_docs.append(doc)
    except Exception as e:
        # Tabula puede lanzar errores si Java no está instalado o si el PDF es problemático
        print(f"  Advertencia: No se pudieron extraer tablas de {os.path.basename(pdf_path)} con Tabula. Error: {e}")
        
    return table_docs

# --- Script Principal de Ingesta Enriquecida ---
if __name__ == "__main__":
    start_total_time = time.time()



    if not os.path.exists(SOURCE_DIRECTORY):
        print(f"Error: El directorio fuente '{SOURCE_DIRECTORY}' no existe.")
        exit()

    all_chunks = []

    # 7. Crear y Guardar el Vector Store FAISS con TODOS los chunks (texto, imágenes, tablas), se sube para garantizar que no se borren las imagenes ETC
    if os.path.exists(PERSIST_DIRECTORY):
        print(f"Borrando directorio de Vector Store existente: {PERSIST_DIRECTORY}")
        shutil.rmtree(PERSIST_DIRECTORY)
    
    # 1. Iterar sobre todos los PDFs en el directorio fuente
    pdf_files = [f for f in os.listdir(SOURCE_DIRECTORY) if f.lower().endswith(".pdf")]
    
    for pdf_filename in pdf_files:
        pdf_path = os.path.join(SOURCE_DIRECTORY, pdf_filename)
        print(f"\n--- Procesando documento: {pdf_filename} ---")

        # 2. Extraer texto completo del PDF
        doc_fitz = fitz.open(pdf_path)
        full_text = ""
        for page in doc_fitz:
            full_text += page.get_text()
        doc_fitz.close()
        
        if not full_text.strip():
            print(f"  Advertencia: No se pudo extraer texto de {pdf_filename}.")
            # Continuar con el siguiente archivo, pero aún intentar extraer imágenes/tablas
        
        # 3. Crear chunks de texto
        if full_text.strip():
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
            text_chunks_docs = text_splitter.create_documents([full_text])
            
            for chunk in text_chunks_docs:
                chunk.metadata["source"] = pdf_filename
                chunk.metadata["content_type"] = "text"
            
            all_chunks.extend(text_chunks_docs)
            print(f"  Generados {len(text_chunks_docs)} chunks de texto.")

        # 4. Extraer imágenes y crear "chunks de imagen"
        print(f"  Extrayendo imágenes de {pdf_filename}...")
        images_info = extract_images_from_pdf(pdf_path, IMAGE_OUTPUT_DIRECTORY)
        
        if images_info:
            print(f"  Encontradas {len(images_info)} imágenes. Creando chunks de descripción...")
            for img_meta in images_info:
                caption, figure_id = find_caption_for_image(full_text, img_meta["page"], img_meta["source_doc"])
                image_chunk = Document(
                    page_content=caption,
                    metadata={
                        "source": img_meta["source_doc"],
                        "page": img_meta["page"],
                        "content_type": "image_description",
                        "image_path": img_meta["image_path"],
                        "figure_id": figure_id
                    }
                )
                all_chunks.append(image_chunk)
            print(f"  Añadidos {len(images_info)} chunks de descripción de imagen.")

        # 5. Extraer tablas y crear "chunks de tabla"
        table_docs = extract_tables_as_docs(pdf_path)
        if table_docs:
            all_chunks.extend(table_docs)
            print(f"  Añadidos {len(table_docs)} chunks de tabla.")
            
    if not all_chunks:
        print("No se generaron chunks de ningún documento. Saliendo.")
        exit()

    # 6. Inicializar Embeddings
    print(f"\nInicializando modelo de embedding: {MODEL_NAME_EMBEDDING}...")
    embeddings_model = HuggingFaceEmbeddings(
        model_name=MODEL_NAME_EMBEDDING,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )


    print(f"\nCreando índice FAISS a partir de {len(all_chunks)} chunks totales...")
    start_db_time = time.time()
    vectorstore = FAISS.from_documents(
        documents=all_chunks,
        embedding=embeddings_model
    )
    end_db_time = time.time()
    print(f"¡Índice FAISS creado en {end_db_time - start_db_time:.2f} segundos!")

    print(f"Guardando índice FAISS en disco en: {PERSIST_DIRECTORY}")
    vectorstore.save_local(PERSIST_DIRECTORY)
    print("¡Índice guardado!")

    end_total_time = time.time()
    print(f"\nProceso de ingesta multimodal completado en {end_total_time - start_total_time:.2f} segundos.")

