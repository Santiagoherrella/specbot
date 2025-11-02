"""
database_supabase.py - Módulo de gestión de base de datos PostgreSQL (Supabase)
Almacena el historial de análisis de PDFs en Supabase.
Detecta automáticamente si está en modo desarrollo o producción.
"""

import os
import psycopg2
from datetime import datetime
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Detectar el entorno
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

def is_production():
    """Verifica si la aplicación está corriendo en producción"""
    return ENVIRONMENT.lower() == "production"

def get_db_connection():
    """Crea y retorna una conexión a la base de datos"""
    try:
        # Intenta obtener desde st.secrets (Streamlit Cloud)
        import streamlit as st
        conn_string = st.secrets["DATABASE_URL"]
    except:
        # Si no está en Streamlit, usa variable de entorno
        conn_string = os.getenv("DATABASE_URL")
    
    if not conn_string:
        raise ValueError("No se encontró DATABASE_URL en secrets o variables de entorno")
    
    conn = psycopg2.connect(conn_string)
    return conn

def init_database():
    """
    Inicializa la base de datos y crea la tabla si no existe.
    Se ejecuta al inicio de la aplicación.
    """
    if not is_production():
        print("⚠️ MODO DESARROLLO - Base de datos no se inicializará")
        return
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Crear tabla con columnas adicionales para las tablas generadas
        cur.execute("""
            CREATE TABLE IF NOT EXISTS analisis_pdfs (
                id SERIAL PRIMARY KEY,
                nombre_archivo TEXT NOT NULL,
                resumen TEXT NOT NULL,
                tablas_tecnicas TEXT,
                fecha_analisis TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Agregar columna si no existe (para bases de datos existentes)
        cur.execute("""
            DO $$ 
            BEGIN 
                BEGIN
                    ALTER TABLE analisis_pdfs ADD COLUMN tablas_tecnicas TEXT;
                EXCEPTION
                    WHEN duplicate_column THEN 
                        NULL;
                END;
            END $$;
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Base de datos inicializada correctamente (PRODUCCIÓN)")
    except Exception as e:
        print(f"❌ Error al inicializar base de datos: {e}")

def guardar_analisis(nombre_archivo, resumen, tablas=None):
    """
    Guarda el análisis en la base de datos (solo en producción).
    """
    if not is_production():
        print(f"⚠️ MODO DESARROLLO - No se guardará en base de datos: {nombre_archivo}")
        return True
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            """
            INSERT INTO analisis_pdfs (nombre_archivo, resumen, tablas_tecnicas)
            VALUES (%s, %s, %s)
            """,
            (nombre_archivo, resumen, tablas)
        )
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Análisis guardado en base de datos (PRODUCCIÓN): {nombre_archivo}")
        return True
    except Exception as e:
        print(f"❌ Error al guardar en base de datos: {e}")
        return False

def buscar_por_nombre_pdf(nombre_archivo):
    """
    Busca análisis previos por nombre de archivo (solo en producción).
    """
    if not is_production():
        print(f"⚠️ MODO DESARROLLO - No se buscará en base de datos: {nombre_archivo}")
        return None
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute(
            """
            SELECT * FROM analisis_pdfs 
            WHERE nombre_archivo = %s 
            ORDER BY fecha_analisis DESC 
            LIMIT 1
            """,
            (nombre_archivo,)
        )
        
        resultado = cur.fetchone()
        cur.close()
        conn.close()
        
        if resultado:
            print(f"✅ Análisis previo encontrado (PRODUCCIÓN): {nombre_archivo}")
        
        return resultado
    except Exception as e:
        print(f"❌ Error al buscar en base de datos: {e}")
        return None

def obtener_historial(limite=50):
    """
    Obtiene el historial de análisis (solo en producción).
    """
    if not is_production():
        print("⚠️ MODO DESARROLLO - No hay historial disponible")
        return []
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute(
            """
            SELECT * FROM analisis_pdfs 
            ORDER BY fecha_analisis DESC 
            LIMIT %s
            """,
            (limite,)
        )
        
        resultados = cur.fetchall()
        cur.close()
        conn.close()
        
        return resultados
    except Exception as e:
        print(f"❌ Error al obtener historial: {e}")
        return []